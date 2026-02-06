package explicit.architecture.extractor.model;

import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;

/**
 * 与 Python 侧 semantic_coupling.models.ModuleRecord 对齐的结构。
 *
 * id:
 *   fully-qualified class name, e.g. "com.example.user.UserService"
 * text:
 *   用于词汇 / 语义表示的文本（类名、方法名、字段名、注释等简单拼接）
 * deps:
 *   edge_type -> { target_module_id -> count }
 * 
 * 新增字段（模块级别分析）：
 * - 模块规模特征：methodCount, fieldCount, lineCount, commentRatio, textLength, vocabularyDiversity
 * - 依赖密度：outDegreeByType, inDegreeByType, weightedDependencyStrength
 */
public class ModuleRecord {

    public String id;
    public String text;
    public Map<String, Map<String, Integer>> deps = new HashMap<>();

    // 模块规模特征
    public int methodCount = 0;
    public int fieldCount = 0;
    public int lineCount = 0;
    public double commentRatio = 0.0;  // 注释行数 / 总行数
    public int textLength = 0;  // Token 数（按空格分割）
    public double vocabularyDiversity = 0.0;  // unique token / total token

    // 依赖密度（按类型统计）
    public Map<String, Integer> outDegreeByType = new HashMap<>();  // edge_type -> count
    public Map<String, Integer> inDegreeByType = new HashMap<>();   // edge_type -> count (需要后处理)
    public double weightedDependencyStrength = 0.0;  // sum(deps[type] * edge_type_weights[type])

    public ModuleRecord() {
    }

    public ModuleRecord(String id, String text) {
        this.id = id;
        this.text = text;
        computeTextMetrics();
    }

    public void addDep(String edgeType, String targetId) {
        if (targetId == null || targetId.isEmpty()) {
            return;
        }
        deps.computeIfAbsent(edgeType, k -> new HashMap<>())
                .merge(targetId, 1, Integer::sum);
        // 更新出度统计
        outDegreeByType.merge(edgeType, 1, Integer::sum);
    }

    /**
     * 计算文本相关指标：textLength 和 vocabularyDiversity
     */
    private void computeTextMetrics() {
        if (text == null || text.isEmpty()) {
            return;
        }
        String[] tokens = text.trim().split("\\s+");
        textLength = tokens.length;
        if (textLength > 0) {
            Set<String> uniqueTokens = new HashSet<>();
            for (String token : tokens) {
                if (!token.isEmpty()) {
                    uniqueTokens.add(token.toLowerCase());
                }
            }
            vocabularyDiversity = (double) uniqueTokens.size() / textLength;
        }
    }

    /**
     * 设置行数和注释比例（由 ProjectScanner 调用）
     */
    public void setLineMetrics(int totalLines, int commentLines) {
        this.lineCount = totalLines;
        if (totalLines > 0) {
            this.commentRatio = (double) commentLines / totalLines;
        }
    }
}


