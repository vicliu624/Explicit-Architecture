#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
smart_java_splitter_v2.py

SmartJavaSplitterV2
- 基于 Tree-sitter 的智能 Java 代码分割器（多粒度、可学习评分函数雏形）
- 如果 tree-sitter 不可用，提供改进的 fallback 模式
- 支持批处理、缓存、可配置权重和阈值

依赖 (推荐):
    pip install tree-sitter tree-sitter-languages

用法:
    python smart_java_splitter_v2.py --input path/to/File.java --mode best
    python smart_java_splitter_v2.py --input path/to/dir --out_dir ./splits --batch

主要功能:
    - parse -> find candidate split points (AST nodes)
    - score candidates with composite score:
        score = alpha * semantic_weight + beta * balance_score + gamma * token_density_score + delta * depth_score
    - recursive splitting (multi-granularity) if requested
    - validate split results (syntax/brace balance / string/comment safety)
"""

from __future__ import annotations

import os
import sys
import math
import json
import re
import argparse
from dataclasses import dataclass
from enum import Enum
from typing import List, Tuple, Optional, Any, Dict, Iterable
from functools import lru_cache

# Try to import Tree-sitter and language helper
TRY_TREE_SITTER = True
try:
    from tree_sitter import Parser
    from tree_sitter_languages import get_language
    LANG_JAVA = get_language("java")
except Exception as e:
    TRY_TREE_SITTER = False
    LANG_JAVA = None

# ---------- Types ----------
@dataclass
class Candidate:
    line_index: int               # 0-based index where suffix starts
    node_type: str                # tree-sitter node type or 'balanced'/'fallback'
    semantic_weight: float        # base semantic weight (e.g., class/method)
    depth: int                    # AST depth
    token_density: float          # tokens / chars in surrounding region
    description: str = ""
    is_semantic_boundary: bool = False
    score: float = 0.0            # final composite score

@dataclass
class SplitResult:
    prefix: str
    suffix: str
    split_line: int               # 0-based
    candidate: Candidate

# ---------- Utility functions ----------
_token_re = re.compile(r"\w+")

def simple_token_count(text: str) -> int:
    return len(_token_re.findall(text))

def clamp(x, a, b):
    return a if x < a else b if x > b else x

# ---------- Smart splitter ----------
class SmartJavaSplitterV2:
    """
    SmartJavaSplitterV2:
      - parser: Tree-sitter Parser if available
      - config: scoring weights and thresholds
    """
    DEFAULT_WEIGHTS = {
        'class': 10.0,
        'method': 8.0,
        'constructor': 7.0,
        'field': 4.0,
        'block': 5.0,
        'control': 3.5,
        'statement': 2.0,
        'balanced': 1.0
    }

    def __init__(self,
                 use_tree_sitter: bool = TRY_TREE_SITTER,
                 min_prefix_chars: int = 40,
                 min_suffix_chars: int = 40,
                 min_split_ratio: float = 0.08,
                 max_split_ratio: float = 0.92,
                 scoring_params: Optional[Dict[str, float]] = None):
        self.use_tree_sitter = use_tree_sitter and (LANG_JAVA is not None)
        self.parser = None
        if self.use_tree_sitter:
            try:
                self.parser = Parser()
                self.parser.set_language(LANG_JAVA)
            except Exception:
                self.parser = None
                self.use_tree_sitter = False

        self.min_prefix_chars = min_prefix_chars
        self.min_suffix_chars = min_suffix_chars
        self.min_split_ratio = min_split_ratio
        self.max_split_ratio = max_split_ratio

        # scoring mixture hyperparams
        if scoring_params is None:
            scoring_params = {
                'alpha_semantic': 1.0,
                'beta_balance': 1.0,
                'gamma_density': 0.5,
                'delta_depth': 0.3
            }
        self.scoring_params = scoring_params

        self.semantic_weights = SmartJavaSplitterV2.DEFAULT_WEIGHTS

    # ----------------- Public API -----------------
    def split_file(self, source: str, mode: str = 'best', recursive: bool = False) -> Optional[List[SplitResult]]:
        """
        Split a Java source (string) into prefix/suffix pairs.
        mode: 'best' -> return best single split; 'candidates' -> return scored candidates list
        recursive: if True, perform multi-granularity recursive splits (returns list of results)
        """
        lines = source.splitlines(keepends=True)
        if len(lines) < 3:
            return None

        content = source

        # parse and get candidates
        if self.use_tree_sitter and self.parser:
            try:
                tree = self.parser.parse(bytes(content, 'utf8'))
                root = tree.root_node
                candidates = self._candidates_from_ast(root, content, lines)
            except Exception as e:
                # fallback to regex-based
                candidates = self._candidates_from_fallback(content, lines)
        else:
            candidates = self._candidates_from_fallback(content, lines)

        if not candidates:
            # add balanced mid point
            mid = len(lines) // 2
            candidates = [Candidate(line_index=mid,
                                    node_type='balanced',
                                    semantic_weight=self.semantic_weights['balanced'],
                                    depth=0,
                                    token_density=0.0,
                                    description='balanced fallback',
                                    is_semantic_boundary=False)]

        # score candidates
        self._score_candidates(candidates, content, lines)

        # filter valid splits
        valid = [c for c in candidates if self._is_valid_split_candidate(c, content, lines)]
        if not valid:
            # attempt relaxing thresholds by allowing shorter suffix/prefix
            valid = [c for c in candidates if self._is_valid_split_candidate(c, content, lines, relax=True)]

        if not valid:
            return None

        # choose best or return all candidates
        valid.sort(key=lambda x: x.score, reverse=True)

        results = []
        if mode == 'candidates':
            for c in valid:
                prefix = ''.join(lines[:c.line_index])
                suffix = ''.join(lines[c.line_index:])
                results.append(SplitResult(prefix=prefix, suffix=suffix, split_line=c.line_index, candidate=c))
            return results

        # mode == 'best'
        best = valid[0]
        prefix = ''.join(lines[:best.line_index])
        suffix = ''.join(lines[best.line_index:])

        if not self._validate_split_result(prefix, suffix):
            # try next best
            for c in valid[1:]:
                p = ''.join(lines[:c.line_index])
                s = ''.join(lines[c.line_index:])
                if self._validate_split_result(p, s):
                    best = c
                    prefix, suffix = p, s
                    break
            else:
                # none validate: return None
                return None

        results.append(SplitResult(prefix=prefix, suffix=suffix, split_line=best.line_index, candidate=best))

        if recursive:
            # recursive: attempt to split prefix and suffix further (method-level)
            # we return aggregate list: first level chosen split then optional recursive splits
            rec = []
            # try splitting prefix into smaller chunks (only if large)
            if len(prefix) > 2 * self.min_prefix_chars:
                nested = self.split_file(prefix, mode='best', recursive=False)
                if nested:
                    rec.extend(nested)
            # try splitting suffix similarly
            if len(suffix) > 2 * self.min_suffix_chars:
                nested = self.split_file(suffix, mode='best', recursive=False)
                if nested:
                    rec.extend(nested)
            results.extend(rec)

        return results

    def batch_split_paths(self, paths: Iterable[str], out_dir: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """
        Batch process file paths or directories. Returns a dict mapping path -> split metadata.
        If out_dir provided, saves split pairs as files.
        """
        results = {}
        for path in paths:
            if os.path.isdir(path):
                for root, _, files in os.walk(path):
                    for f in files:
                        if f.endswith('.java'):
                            full = os.path.join(root, f)
                            r = self._process_file_path(full, out_dir, **kwargs)
                            results[full] = r
            elif os.path.isfile(path):
                r = self._process_file_path(path, out_dir, **kwargs)
                results[path] = r
        return results

    # ----------------- Internals: Candidate extraction -----------------
    def _candidates_from_ast(self, root_node, content: str, lines: List[str]) -> List[Candidate]:
        """
        Traverse the AST and produce split candidates.
        Uses node types from tree-sitter-java grammar.
        """
        candidates: List[Candidate] = []

        def traverse(node, depth=0):
            # ignore anonymous class bodies and comments
            try:
                node_type = node.type
            except Exception:
                return

            start_line = node.start_point[0]  # 0-based
            # map node types to semantic categories
            if node_type in ('class_declaration', 'normal_interface_declaration', 'enum_declaration', 'record_declaration'):
                candidates.append(Candidate(line_index=self._line_after_node(node, lines),
                                            node_type=node_type,
                                            semantic_weight=self.semantic_weights.get('class', 10.0),
                                            depth=depth,
                                            token_density=self._token_density_around(node, content),
                                            description=f'After {node_type}',
                                            is_semantic_boundary=True))
            elif node_type in ('method_declaration',):
                candidates.append(Candidate(line_index=self._line_after_node(node, lines),
                                            node_type=node_type,
                                            semantic_weight=self.semantic_weights.get('method', 8.0),
                                            depth=depth,
                                            token_density=self._token_density_around(node, content),
                                            description='After method',
                                            is_semantic_boundary=True))
            elif node_type in ('constructor_declaration',):
                candidates.append(Candidate(line_index=self._line_after_node(node, lines),
                                            node_type=node_type,
                                            semantic_weight=self.semantic_weights.get('constructor', 7.0),
                                            depth=depth,
                                            token_density=self._token_density_around(node, content),
                                            description='After constructor',
                                            is_semantic_boundary=True))
            elif node_type in ('field_declaration',):
                candidates.append(Candidate(line_index=self._line_after_node(node, lines),
                                            node_type=node_type,
                                            semantic_weight=self.semantic_weights.get('field', 4.0),
                                            depth=depth,
                                            token_density=self._token_density_around(node, content),
                                            description='After field',
                                            is_semantic_boundary=False))
            elif node_type.endswith('_statement') or node_type in ('if_statement', 'for_statement', 'while_statement', 'try_statement', 'switch_expression', 'switch_statement'):
                candidates.append(Candidate(line_index=self._line_after_node(node, lines),
                                            node_type=node_type,
                                            semantic_weight=self.semantic_weights.get('control', 3.5),
                                            depth=depth,
                                            token_density=self._token_density_around(node, content),
                                            description=f'After {node_type}',
                                            is_semantic_boundary=False))
            elif node_type in ('expression_statement',):
                candidates.append(Candidate(line_index=self._line_after_node(node, lines),
                                            node_type=node_type,
                                            semantic_weight=self.semantic_weights.get('statement', 2.0),
                                            depth=depth,
                                            token_density=self._token_density_around(node, content),
                                            description='After expression stmt',
                                            is_semantic_boundary=False))
            # recurse children
            for c in node.children:
                traverse(c, depth + 1)

        traverse(root_node, 0)

        # if no semantic splits, include balanced mid
        if not candidates:
            mid = len(lines) // 2
            candidates.append(Candidate(line_index=mid,
                                        node_type='balanced',
                                        semantic_weight=self.semantic_weights.get('balanced', 1.0),
                                        depth=0,
                                        token_density=0.0,
                                        description='balanced default',
                                        is_semantic_boundary=False))
        return candidates

    def _candidates_from_fallback(self, content: str, lines: List[str]) -> List[Candidate]:
        """
        More robust fallback using regex but improved:
        - find class/method/constructor/field patterns, but then compute an approximate line
        """
        candidates: List[Candidate] = []
        # class
        class_pat = re.compile(r'(?:public|protected|private)?\s*(?:abstract|final|sealed|static)?\s*(class|interface|enum|record|@interface)\s+\w+', re.M)
        for m in class_pat.finditer(content):
            ln = content[:m.end()].count('\n')
            candidates.append(Candidate(line_index=min(ln + 1, len(lines)-1),
                                        node_type='class_declaration',
                                        semantic_weight=self.semantic_weights.get('class', 10.0),
                                        depth=1,
                                        token_density=self._approx_token_density(content, m.start(), m.end()),
                                        description='fallback class',
                                        is_semantic_boundary=True))
        # method
        method_pat = re.compile(r'(?:public|protected|private)?\s*(?:static|final|synchronized|native|strictfp|default)?\s*(?:<[^>]*>)?\s*(?:[\w\[\]\<\>]+)\s+(\w+)\s*\([^;{)]*\)\s*(?:throws\s+[^{;]+)?\s*[{;]', re.M)
        for m in method_pat.finditer(content):
            ln = content[:m.end()].count('\n')
            candidates.append(Candidate(line_index=min(ln + 1, len(lines)-1),
                                        node_type='method_declaration',
                                        semantic_weight=self.semantic_weights.get('method', 8.0),
                                        depth=1,
                                        token_density=self._approx_token_density(content, m.start(), m.end()),
                                        description='fallback method',
                                        is_semantic_boundary=True))
        # constructors
        ctor_pat = re.compile(r'(?:public|protected|private)?\s*([A-Z]\w*)\s*\([^)]*\)\s*(?:throws\s+[^{;]+)?\s*[{;]', re.M)
        for m in ctor_pat.finditer(content):
            ln = content[:m.end()].count('\n')
            candidates.append(Candidate(line_index=min(ln + 1, len(lines)-1),
                                        node_type='constructor_declaration',
                                        semantic_weight=self.semantic_weights.get('constructor', 7.0),
                                        depth=1,
                                        token_density=self._approx_token_density(content, m.start(), m.end()),
                                        description='fallback ctor',
                                        is_semantic_boundary=True))

        # add balanced if none
        if not candidates:
            mid = len(lines) // 2
            candidates.append(Candidate(line_index=mid,
                                        node_type='balanced',
                                        semantic_weight=self.semantic_weights.get('balanced', 1.0),
                                        depth=0,
                                        token_density=0.0,
                                        description='balanced fallback',
                                        is_semantic_boundary=False))
        # deduplicate by line_index (keep max weight)
        by_line: Dict[int, Candidate] = {}
        for c in candidates:
            prev = by_line.get(c.line_index)
            if prev is None or c.semantic_weight > prev.semantic_weight:
                by_line[c.line_index] = c
        return list(by_line.values())

    # ----------------- Scoring -----------------
    def _score_candidates(self, candidates: List[Candidate], content: str, lines: List[str]):
        total_chars = len(content)
        for c in candidates:
            # balance score: how close split is to center (0..1), center->1
            prefix_len = sum(len(l) for l in lines[:c.line_index])
            prefix_ratio = prefix_len / max(1, total_chars)
            balance_score = 1.0 - abs(prefix_ratio - 0.5) * 2.0  # 1 if exactly center, 0 at extremes
            balance_score = clamp(balance_score, 0.0, 1.0)

            # token density normalized: higher density may indicate complex block (we invert to prefer lower density)
            # token_density computed around node: tokens / chars
            td = c.token_density
            # normalize (assume typical td in [0,0.2])
            td_score = 1.0 - clamp(td / 0.15, 0.0, 1.0)  # prefer lower density

            # depth score: shallower nodes preferred for higher-level splits
            depth_score = 1.0 / (1 + c.depth)  # deeper -> smaller

            # combine
            s = (self.scoring_params['alpha_semantic'] * (c.semantic_weight / max(self.semantic_weights.values())) +
                 self.scoring_params['beta_balance'] * balance_score +
                 self.scoring_params['gamma_density'] * td_score +
                 self.scoring_params['delta_depth'] * depth_score)

            # normalize final score to 0..1
            # compute theoretical max = alpha*1 + beta*1 + gamma*1 + delta*1
            denom = (self.scoring_params['alpha_semantic'] +
                     self.scoring_params['beta_balance'] +
                     self.scoring_params['gamma_density'] +
                     self.scoring_params['delta_depth'])
            c.score = s / max(denom, 1e-8)

    # ----------------- Helpers -----------------
    def _line_after_node(self, node, lines: List[str]) -> int:
        """
        Compute the line index after node end, clamp to valid range.
        node.end_point gives (row, col) zero-based; we will take end row + 1
        """
        try:
            end_row = node.end_point[0]
            idx = min(end_row + 1, len(lines) - 1)
            # ensure we don't return 0
            return max(1, idx)
        except Exception:
            return max(1, len(lines)//2)

    def _token_density_around(self, node, content: str, window_chars: int = 200) -> float:
        """
        Compute token density in a window around node start: tokens / chars
        """
        try:
            start = max(0, node.start_byte - window_chars)
            end = min(len(content), node.end_byte + window_chars)
            snippet = content[start:end]
            tokens = simple_token_count(snippet)
            return tokens / max(1, len(snippet))
        except Exception:
            return 0.0

    def _approx_token_density(self, content: str, a: int, b: int, window_chars: int = 200) -> float:
        start = max(0, a - window_chars)
        end = min(len(content), b + window_chars)
        snippet = content[start:end]
        tokens = simple_token_count(snippet)
        return tokens / max(1, len(snippet))

    def _is_valid_split_candidate(self, c: Candidate, content: str, lines: List[str], relax: bool = False) -> bool:
        """
        Validate candidate by length and ratio constraints.
        relax=True reduces min char constraints by half.
        """
        total = len(content)
        prefix_chars = sum(len(l) for l in lines[:c.line_index])
        suffix_chars = total - prefix_chars
        min_pref = self.min_prefix_chars // (2 if relax else 1)
        min_suf = self.min_suffix_chars // (2 if relax else 1)

        if prefix_chars < min_pref or suffix_chars < min_suf:
            return False

        pref_ratio = prefix_chars / total
        if pref_ratio < self.min_split_ratio or pref_ratio > self.max_split_ratio:
            return False
        return True

    def _validate_split_result(self, prefix: str, suffix: str) -> bool:
        """
        Basic validation: bracket matching and not splitting inside an open string/comment.
        If tree-sitter available, attempt to parse both halves separately (best).
        """
        # quick length checks
        if len(prefix.strip()) < self.min_prefix_chars or len(suffix.strip()) < self.min_suffix_chars:
            return False

        # check braces balance: prefix should not require more closing braces than suffix has
        p_open = prefix.count('{')
        p_close = prefix.count('}')
        s_open = suffix.count('{')
        s_close = suffix.count('}')
        if p_open > p_close:
            need = p_open - p_close
            if s_close < need:
                return False

        # check string/comment naive
        if self._is_split_in_string_or_comment(prefix, suffix):
            return False

        # if parser available, try parsing each half as independent compilable fragment:
        if self.use_tree_sitter and self.parser:
            try:
                # parse prefix and suffix; tree-sitter can parse fragments; accept if not catastrophic
                p_tree = self.parser.parse(bytes(prefix, 'utf8'))
                s_tree = self.parser.parse(bytes(suffix, 'utf8'))
                # if trees produce root with reasonable children then pass
                if p_tree.root_node is None or s_tree.root_node is None:
                    return False
            except Exception:
                # don't be too strict if parse fails (fragment code may be unparsable)
                return False
        return True

    def _is_split_in_string_or_comment(self, prefix: str, suffix: str) -> bool:
        """
        Heuristic: ensure prefix not ending inside an open string or comment.
        We do a quick scan for unclosed quotes or comment starts at the end of prefix.
        """
        # check unclosed double/single quotes in prefix
        pre = prefix
        # remove escaped quotes for roughness
        pre_noesc = re.sub(r'\\.', '', pre)
        if pre_noesc.count('"') % 2 == 1 or pre_noesc.count("'") % 2 == 1:
            return True
        # comment starts
        if pre.rstrip().endswith('/*') or pre.rstrip().endswith('//'):
            return True
        return False

    # ----------------- File helpers -----------------
    def _process_file_path(self, path: str, out_dir: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """Process a single file path and optionally write outputs"""
        try:
            with open(path, 'r', encoding='utf8') as f:
                content = f.read()
        except Exception as e:
            return {'ok': False, 'error': str(e)}
        res_list = self.split_file(content, **kwargs)
        if not res_list:
            return {'ok': False, 'error': 'no_split'}
        # write out if requested
        meta = []
        for i, res in enumerate(res_list):
            meta_item = {
                'split_line': res.split_line,
                'candidate': res.candidate.node_type,
                'score': res.candidate.score,
                'description': res.candidate.description
            }
            meta.append(meta_item)
            if out_dir:
                base = os.path.basename(path)
                name = f"{os.path.splitext(base)[0]}_split_{i}.java"
                out_path = os.path.join(out_dir, name)
                os.makedirs(out_dir, exist_ok=True)
                with open(out_path, 'w', encoding='utf8') as wf:
                    wf.write(res.prefix)
                    wf.write('\n/* --- SUFFIX START --- */\n')
                    wf.write(res.suffix)
        return {'ok': True, 'meta': meta}

# ---------- CLI ----------
def main_cli():
    parser = argparse.ArgumentParser(description="SmartJavaSplitterV2 - AST-driven Java code splitter")
    parser.add_argument('--input', '-i', required=True, help='Java file or directory or "-" for stdin')
    parser.add_argument('--mode', choices=['best', 'candidates'], default='best')
    parser.add_argument('--recursive', action='store_true', help='Attempt recursive splitting')
    parser.add_argument('--out_dir', help='If provided, write split outputs')
    parser.add_argument('--batch', action='store_true', help='Treat input as directory/batch when directory')
    parser.add_argument('--min_prefix_chars', type=int, default=40)
    parser.add_argument('--min_suffix_chars', type=int, default=40)
    parser.add_argument('--alpha', type=float, default=1.0)
    parser.add_argument('--beta', type=float, default=1.0)
    parser.add_argument('--gamma', type=float, default=0.5)
    parser.add_argument('--delta', type=float, default=0.3)
    args = parser.parse_args()

    scoring_params = {'alpha_semantic': args.alpha, 'beta_balance': args.beta, 'gamma_density': args.gamma, 'delta_depth': args.delta}

    splitter = SmartJavaSplitterV2(use_tree_sitter=TRY_TREE_SITTER,
                                   min_prefix_chars=args.min_prefix_chars,
                                   min_suffix_chars=args.min_suffix_chars,
                                   scoring_params=scoring_params)

    inp = args.input
    if inp == '-':
        source = sys.stdin.read()
        results = splitter.split_file(source, mode=args.mode, recursive=args.recursive)
        if not results:
            print("No split found")
            sys.exit(1)
        # print best
        for r in results:
            print("=== SPLIT ===")
            print(f"line: {r.split_line}, node: {r.candidate.node_type}, score: {r.candidate.score:.4f}")
            print("--- PREFIX ---")
            print(r.prefix)
            print("--- SUFFIX ---")
            print(r.suffix)
    else:
        if os.path.isdir(inp) and args.batch:
            out_dir = args.out_dir
            os.makedirs(out_dir, exist_ok=True) if out_dir else None
            res = splitter.batch_split_paths([inp], out_dir=out_dir, mode=args.mode, recursive=args.recursive)
            print(json.dumps(res, indent=2))
        elif os.path.isfile(inp):
            with open(inp, 'r', encoding='utf8') as f:
                source = f.read()
            results = splitter.split_file(source, mode=args.mode, recursive=args.recursive)
            if not results:
                print("No split found")
                sys.exit(1)
            for r in results:
                print("=== SPLIT ===")
                print(f"line: {r.split_line}, node: {r.candidate.node_type}, score: {r.candidate.score:.4f}")
                print("--- PREFIX (first 300 chars) ---")
                print(r.prefix[:300])
                print("--- SUFFIX (first 300 chars) ---")
                print(r.suffix[:300])
                if args.out_dir:
                    splitter._process_file_path(inp, out_dir=args.out_dir, mode=args.mode, recursive=args.recursive)
        else:
            print("Input is not a file or directory. Use --batch for directory processing.")
            sys.exit(1)

if __name__ == "__main__":
    main_cli()
