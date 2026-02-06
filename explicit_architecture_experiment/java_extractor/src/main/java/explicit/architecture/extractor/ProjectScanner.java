package explicit.architecture.extractor;

import com.github.javaparser.StaticJavaParser;
import com.github.javaparser.ast.CompilationUnit;
import com.github.javaparser.ast.ImportDeclaration;
import com.github.javaparser.ast.body.ClassOrInterfaceDeclaration;
import com.github.javaparser.ast.body.FieldDeclaration;
import com.github.javaparser.ast.body.MethodDeclaration;
import com.github.javaparser.ast.expr.MethodCallExpr;
import com.github.javaparser.ast.expr.ObjectCreationExpr;
import com.github.javaparser.ast.visitor.VoidVisitorAdapter;
import com.github.javaparser.resolution.declarations.ResolvedConstructorDeclaration;
import com.github.javaparser.resolution.declarations.ResolvedMethodDeclaration;
import com.github.javaparser.resolution.types.ResolvedType;
import explicit.architecture.extractor.model.ModuleRecord;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;

/**
 * 从给定的 src 根目录扫描 Java 源文件，抽取类级依赖信息。
 *
 * 最小可用版：
 *  - 一个顶级类 => 一个 ModuleRecord
 *  - id:  package + "." + className
 *  - text: 类名 + 字段名 + 方法名 + 参数名 + Javadoc 文本
 *  - deps:
 *      - inherit: extends / implements 的类型
 *      - field:   字段类型
 *      - call:    方法体中的方法调用 / 构造调用的声明类型
 *      - static_import: 静态导入所在的类型
 */
public final class ProjectScanner {

    private ProjectScanner() {
    }

    public static List<ModuleRecord> scanProject(Path srcRoot) throws IOException {
        List<ModuleRecord> modules = new ArrayList<>();

        Files.walk(srcRoot)
                .filter(p -> p.toString().endsWith(".java"))
                .forEach(p -> {
                    try {
                        // 用文件内容而不是 StaticJavaParser.parse(Path)，
                        // 以避免编码问题。
                        String code = Files.readString(p, StandardCharsets.UTF_8);
                        CompilationUnit cu = StaticJavaParser.parse(code);
                        scanCompilationUnit(cu, code, modules);
                    } catch (Exception e) {
                        System.err.println("Failed to parse " + p + ": " + e.getMessage());
                    }
                });

        return modules;
    }

    private static void scanCompilationUnit(CompilationUnit cu, String sourceCode, List<ModuleRecord> modules) {
        String pkg = cu.getPackageDeclaration()
                .map(pd -> pd.getNameAsString())
                .orElse("");

        // 计算文件总行数和注释行数
        String[] lines = sourceCode.split("\n");
        final int totalLines = lines.length;
        int commentLinesCount = 0;
        for (String line : lines) {
            String trimmed = line.trim();
            if (trimmed.startsWith("//") || trimmed.startsWith("/*") || trimmed.startsWith("*")) {
                commentLinesCount++;
            }
        }
        // 也统计块注释
        final int commentLines = commentLinesCount + cu.getAllContainedComments().size();

        // 静态 import 对应的类型（粗略版：去掉最后一节方法 / 字段名）
        List<String> staticImportTypes = new ArrayList<>();
        for (ImportDeclaration imp : cu.getImports()) {
            if (imp.isStatic()) {
                String q = imp.getName().asString();
                int idx = q.lastIndexOf('.');
                if (idx > 0) {
                    staticImportTypes.add(q.substring(0, idx));
                }
            }
        }

        cu.findAll(ClassOrInterfaceDeclaration.class).forEach(cls -> {
            if (!cls.isTopLevelType()) {
                return;
            }

            String className = cls.getNameAsString();
            String id = pkg.isEmpty() ? className : pkg + "." + className;

            // text: 提取更丰富的语义信息
            // 包括：类名、字段（名称+类型）、方法（名称+返回类型+参数）、Javadoc、行内注释
            StringBuilder text = new StringBuilder();
            
            // 类名和修饰符
            text.append(className).append(' ');
            cls.getModifiers().forEach(m -> text.append(m.getKeyword().asString()).append(' '));
            
            // 类的 Javadoc（完整内容）
            cls.getJavadocComment().ifPresent(c -> {
                String javadoc = c.getContent();
                // 清理 Javadoc 标记，保留实际内容
                javadoc = javadoc.replaceAll("\\*+", " ").replaceAll("\\s+", " ").trim();
                text.append(javadoc).append(' ');
            });
            
            // 统计字段数
            int fieldCount = 0;
            // 字段：名称 + 类型
            for (FieldDeclaration field : cls.getFields()) {
                fieldCount += field.getVariables().size();
                // 字段类型
                text.append(field.getElementType().asString()).append(' ');
                // 字段名称
                field.getVariables().forEach(v -> {
                    text.append(v.getNameAsString()).append(' ');
                    // 字段的注释（如果有）
                    v.getComment().ifPresent(comment -> {
                        String commentText = comment.getContent();
                        commentText = commentText.replaceAll("\\*+", " ").replaceAll("\\s+", " ").trim();
                        text.append(commentText).append(' ');
                    });
                });
            }
            
            // 统计方法数
            int methodCount = cls.getMethods().size();
            // 方法：名称 + 返回类型 + 参数类型 + 参数名 + Javadoc
            for (MethodDeclaration m : cls.getMethods()) {
                // 方法名
                text.append(m.getNameAsString()).append(' ');
                
                // 返回类型
                if (!m.getType().isVoidType()) {
                    text.append(m.getType().asString()).append(" returns ").append(' ');
                }
                
                // 参数类型和名称
                m.getParameters().forEach(p -> {
                    text.append(p.getType().asString()).append(' ');
                    text.append(p.getNameAsString()).append(' ');
                });
                
                // 方法的 Javadoc
                m.getJavadocComment().ifPresent(c -> {
                    String javadoc = c.getContent();
                    javadoc = javadoc.replaceAll("\\*+", " ").replaceAll("\\s+", " ").trim();
                    text.append(javadoc).append(' ');
                });
            }
            
            // 类的行内注释（如果有）
            cls.getComment().ifPresent(comment -> {
                String commentText = comment.getContent();
                commentText = commentText.replaceAll("//", " ").replaceAll("/\\*", " ").replaceAll("\\*/", " ")
                        .replaceAll("\\s+", " ").trim();
                text.append(commentText).append(' ');
            });

            ModuleRecord mr = new ModuleRecord(id, text.toString());
            
            // 设置模块规模特征
            mr.methodCount = methodCount;
            mr.fieldCount = fieldCount;
            mr.setLineMetrics(totalLines, commentLines);

            // inherit: extends / implements
            cls.getExtendedTypes().forEach(t -> {
                try {
                    ResolvedType rt = t.resolve();
                    if (rt.isReferenceType()) {
                        mr.addDep("inherit", rt.asReferenceType().getQualifiedName());
                    }
                } catch (Exception ignored) {
                }
            });
            cls.getImplementedTypes().forEach(t -> {
                try {
                    ResolvedType rt = t.resolve();
                    if (rt.isReferenceType()) {
                        mr.addDep("inherit", rt.asReferenceType().getQualifiedName());
                    }
                } catch (Exception ignored) {
                }
            });

            // field: 字段类型
            for (FieldDeclaration field : cls.getFields()) {
                field.getElementType().ifClassOrInterfaceType(cit -> {
                    try {
                        ResolvedType rt = cit.resolve();
                        if (rt.isReferenceType()) {
                            mr.addDep("field", rt.asReferenceType().getQualifiedName());
                        }
                    } catch (Exception ignored) {
                    }
                });
            }

            // static_import: 类型名
            for (String t : staticImportTypes) {
                mr.addDep("static_import", t);
            }

            // call: 方法体中的调用 / 构造
            cls.accept(new VoidVisitorAdapter<ModuleRecord>() {
                @Override
                public void visit(MethodCallExpr n, ModuleRecord collector) {
                    super.visit(n, collector);
                    try {
                        ResolvedMethodDeclaration rmd = n.resolve();
                        String declaringType = rmd.declaringType().getQualifiedName();
                        collector.addDep("call", declaringType);
                    } catch (Exception ignored) {
                    }
                }

                @Override
                public void visit(ObjectCreationExpr n, ModuleRecord collector) {
                    super.visit(n, collector);
                    try {
                        ResolvedConstructorDeclaration rcd = n.resolve();
                        String declaringType = rcd.declaringType().getQualifiedName();
                        collector.addDep("call", declaringType);
                    } catch (Exception ignored) {
                    }
                }
            }, mr);

            modules.add(mr);
        });
    }
}


