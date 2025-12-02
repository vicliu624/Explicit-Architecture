package explicit.architecture.extractor;

import com.github.javaparser.ParserConfiguration;
import com.github.javaparser.StaticJavaParser;
import com.github.javaparser.symbolsolver.JavaSymbolSolver;
import com.github.javaparser.symbolsolver.resolution.typesolvers.CombinedTypeSolver;
import com.github.javaparser.symbolsolver.resolution.typesolvers.JavaParserTypeSolver;
import com.github.javaparser.symbolsolver.resolution.typesolvers.ReflectionTypeSolver;

import java.nio.file.Path;

/**
 * 配置 JavaParser + SymbolSolver，用于从源码解析出 FQCN。
 */
public final class ParserConfig {

    private ParserConfig() {
    }

    public static void configure(Path projectRoot) {
        CombinedTypeSolver typeSolver = new CombinedTypeSolver();

        // 工程源码
        typeSolver.add(new JavaParserTypeSolver(projectRoot.toFile()));
        // JDK / 标准库
        typeSolver.add(new ReflectionTypeSolver(false));

        ParserConfiguration config = new ParserConfiguration()
                // 支持 record / instanceof pattern 等新语法
                .setLanguageLevel(ParserConfiguration.LanguageLevel.JAVA_21)
                .setSymbolResolver(new JavaSymbolSolver(typeSolver));
        StaticJavaParser.setConfiguration(config);
    }
}


