package explicit.architecture.extractor.model;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * 与 Python 侧 load_modules_from_json 约定的顶层 JSON 结构对齐。
 * 
 * 新增项目级别统计信息。
 */
public class ProjectModules {

    public Map<String, Double> edge_type_weights;
    public List<ModuleRecord> modules;
    public ProjectStats projectStats;  // 项目级别统计

    /**
     * 项目级别统计信息
     */
    public static class ProjectStats {
        // 模块规模统计
        public int totalModules = 0;
        public double avgMethodCount = 0.0;
        public double avgFieldCount = 0.0;
        public double avgLineCount = 0.0;
        public double avgCommentRatio = 0.0;
        public double avgTextLength = 0.0;
        public double avgVocabularyDiversity = 0.0;

        // 依赖类型贡献分析
        public Map<String, Integer> dependencyTypeContribution = new LinkedHashMap<>();

        // 加权依赖强度统计
        public double avgWeightedDependencyStrength = 0.0;
    }
}


