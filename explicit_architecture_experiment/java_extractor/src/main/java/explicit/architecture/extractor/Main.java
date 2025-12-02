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

        ProjectModules pm = new ProjectModules();

        Map<String, Double> weights = new LinkedHashMap<>();
        weights.put("call", 1.0);
        weights.put("field", 0.8);
        weights.put("inherit", 0.9);
        weights.put("static_import", 0.6);
        pm.edge_type_weights = weights;
        pm.modules = modules;

        ObjectMapper mapper = new ObjectMapper().enable(SerializationFeature.INDENT_OUTPUT);
        mapper.writeValue(outJson.toFile(), pm);

        System.out.println("Wrote " + modules.size() + " modules to " + outJson);
    }
}


