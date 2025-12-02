package explicit.architecture.extractor.model;

import java.util.List;
import java.util.Map;

/**
 * 与 Python 侧 load_modules_from_json 约定的顶层 JSON 结构对齐。
 */
public class ProjectModules {

    public Map<String, Double> edge_type_weights;
    public List<ModuleRecord> modules;
}


