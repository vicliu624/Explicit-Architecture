package explicit.architecture.extractor;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.SerializationFeature;
import explicit.architecture.extractor.model.ModuleRecord;
import explicit.architecture.extractor.model.ProjectModules;

import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * 最小可用的 Java 抽取器：
 *
 * Usage:
 *   mvn -q -DskipTests package
 *   java -jar target/java-extractor-0.1.0-SNAPSHOT-jar-with-dependencies.jar \\
 *       /path/to/java/project/src/main/java \\
 *       /path/to/java/project/project_modules.json
 *
 * 生成的 JSON 与 Python 侧 semantic_coupling.io.load_modules_from_json 兼容。
 */
public class Main {

    public static void main(String[] args) throws Exception {
        if (args.length < 2) {
            System.err.println("Usage: java -jar java-extractor.jar <src-root> <output-json>");
            System.exit(1);
        }

        Path srcRoot = Paths.get(args[0]).toAbsolutePath().normalize();
        Path outJson = Paths.get(args[1]).toAbsolutePath().normalize();

        System.out.println("Scanning Java sources under: " + srcRoot);
        ParserConfig.configure(srcRoot);

        List<ModuleRecord> modules = new ArrayList<>(ProjectScanner.scanProject(srcRoot));

        Map<String, Double> weights = new LinkedHashMap<>();
        weights.put("call", 1.0);
        weights.put("field", 0.8);
        weights.put("inherit", 0.9);
        weights.put("static_import", 0.6);

        // 计算加权依赖强度和入度统计
        computeDependencyMetrics(modules, weights);

        ProjectModules pm = new ProjectModules();
        pm.edge_type_weights = weights;
        pm.modules = modules;
        
        // 计算项目级别统计
        pm.projectStats = computeProjectStats(modules, weights);

        ObjectMapper mapper = new ObjectMapper().enable(SerializationFeature.INDENT_OUTPUT);
        mapper.writeValue(outJson.toFile(), pm);

        System.out.println("Wrote " + modules.size() + " modules to " + outJson);
    }

    /**
     * 计算每个模块的加权依赖强度和入度统计
     */
    private static void computeDependencyMetrics(List<ModuleRecord> modules, Map<String, Double> weights) {
        // 构建模块 ID 到索引的映射
        Map<String, Integer> idToIndex = new LinkedHashMap<>();
        for (int i = 0; i < modules.size(); i++) {
            idToIndex.put(modules.get(i).id, i);
        }

        // 计算入度统计（遍历所有模块的出度）
        for (ModuleRecord module : modules) {
            for (Map.Entry<String, Map<String, Integer>> depEntry : module.deps.entrySet()) {
                String edgeType = depEntry.getKey();
                for (String targetId : depEntry.getValue().keySet()) {
                    Integer targetIndex = idToIndex.get(targetId);
                    if (targetIndex != null) {
                        ModuleRecord target = modules.get(targetIndex);
                        target.inDegreeByType.merge(edgeType, 1, Integer::sum);
                    }
                }
            }
        }

        // 计算加权依赖强度
        for (ModuleRecord module : modules) {
            double weightedStrength = 0.0;
            for (Map.Entry<String, Map<String, Integer>> depEntry : module.deps.entrySet()) {
                String edgeType = depEntry.getKey();
                double weight = weights.getOrDefault(edgeType, 1.0);
                int totalCount = depEntry.getValue().values().stream().mapToInt(Integer::intValue).sum();
                weightedStrength += weight * totalCount;
            }
            module.weightedDependencyStrength = weightedStrength;
        }
    }

    /**
     * 计算项目级别统计信息
     */
    private static ProjectModules.ProjectStats computeProjectStats(
            List<ModuleRecord> modules, Map<String, Double> weights) {
        ProjectModules.ProjectStats stats = new ProjectModules.ProjectStats();
        
        if (modules.isEmpty()) {
            return stats;
        }

        // 模块规模统计
        stats.totalModules = modules.size();
        stats.avgMethodCount = modules.stream().mapToInt(m -> m.methodCount).average().orElse(0.0);
        stats.avgFieldCount = modules.stream().mapToInt(m -> m.fieldCount).average().orElse(0.0);
        stats.avgLineCount = modules.stream().mapToInt(m -> m.lineCount).average().orElse(0.0);
        stats.avgCommentRatio = modules.stream().mapToDouble(m -> m.commentRatio).average().orElse(0.0);
        stats.avgTextLength = modules.stream().mapToInt(m -> m.textLength).average().orElse(0.0);
        stats.avgVocabularyDiversity = modules.stream().mapToDouble(m -> m.vocabularyDiversity).average().orElse(0.0);

        // 依赖类型贡献分析
        Map<String, Integer> totalDepsByType = new LinkedHashMap<>();
        for (ModuleRecord module : modules) {
            for (Map.Entry<String, Integer> entry : module.outDegreeByType.entrySet()) {
                totalDepsByType.merge(entry.getKey(), entry.getValue(), Integer::sum);
            }
        }
        stats.dependencyTypeContribution = totalDepsByType;

        // 加权依赖强度统计
        stats.avgWeightedDependencyStrength = modules.stream()
                .mapToDouble(m -> m.weightedDependencyStrength)
                .average()
                .orElse(0.0);

        return stats;
    }
}


