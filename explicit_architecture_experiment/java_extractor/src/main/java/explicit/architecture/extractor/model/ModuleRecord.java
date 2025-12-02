package explicit.architecture.extractor.model;

import java.util.HashMap;
import java.util.Map;

/**
 * 与 Python 侧 semantic_coupling.models.ModuleRecord 对齐的最小结构。
 *
 * id:
 *   fully-qualified class name, e.g. "com.example.user.UserService"
 * text:
 *   用于词汇 / 语义表示的文本（类名、方法名、字段名、注释等简单拼接）
 * deps:
 *   edge_type -> { target_module_id -> count }
 */
public class ModuleRecord {

    public String id;
    public String text;
    public Map<String, Map<String, Integer>> deps = new HashMap<>();

    public ModuleRecord() {
    }

    public ModuleRecord(String id, String text) {
        this.id = id;
        this.text = text;
    }

    public void addDep(String edgeType, String targetId) {
        if (targetId == null || targetId.isEmpty()) {
            return;
        }
        deps.computeIfAbsent(edgeType, k -> new HashMap<>())
                .merge(targetId, 1, Integer::sum);
    }
}


