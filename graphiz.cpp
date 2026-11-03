
#include <iostream>
#include <fstream>
#include <cstdlib>
#include <sstream>
#include <memory>
#include <string>
#include <array>
#include <stdexcept>

std::string execCommand(const char* cmd) {
    std::array<char, 128> buffer;
    std::string result;
#if defined(_WIN32)
    std::unique_ptr<FILE, decltype(&_pclose)> pipe(_popen(cmd, "r"), _pclose);
#else
    std::unique_ptr<FILE, decltype(&pclose)> pipe(popen(cmd, "r"), pclose);
#endif
    if (!pipe) {
        throw std::runtime_error("Не удалось запустить команду!");
    }
    while (fgets(buffer.data(), buffer.size(), pipe.get()) != nullptr) {
        result += buffer.data();
    }
    return result;
}

int main() {
    setlocale(LC_ALL, "Russian");

    std::string pythonScript = "python qwert.py";

    std::cout << "Сбор зависимостей matplotlib из Python... " << std::endl;
    std::string graphEdges;
    try {
        graphEdges = execCommand(pythonScript.c_str());
    }
    catch (const std::exception& e) {
        std::cerr << "Ошибка при работе с Python: " << e.what() << std::endl;
        return 1;
    }

    std::string dotFileName = "matplotlib_deps.dot";
    std::string outputImageName = "matplotlib_deps.png";
    std::ofstream outFile(dotFileName);

    if (!outFile.is_open()) {
        std::cerr << "Не удалось создать файл .dot!" << std::endl;
        return 1;
    }
    
    std::cout << "Наш тест: " << graphEdges << std::endl;

    outFile << "digraph MatplotlibDependencies {\n"
        << "    // Стилизация\n"
        << "    rankdir=LR; // Слева направо\n"
        << "    node [shape=box, style=\"filled,rounded\", color=\"#1f77b4\", fillcolor=\"#e3f2fd\", fontname=\"Arial\", fontsize=11];\n"
        << "    edge [color=\"#708090\", penwidth=1.5, arrowsize=0.8];\n\n"
        << "    // Подсветка главного узла\n"
        << "    \"matplotlib\" [fillcolor=\"#ff7f0e\", fontcolor=white, style=filled, fontsize=13];\n\n"
        << "    // Связи\n"
        << graphEdges
        << "}" << std::endl;
    outFile.close();

    std::string graphvizCmd = "dot -Tpng " + dotFileName + " -o " + outputImageName;
    int result = std::system(graphvizCmd.c_str());

    if (result == 0) {
        std::cout << "Граф зависимостей сохранен в: " << outputImageName << std::endl;
        // Открываем картинку в системе
#if defined(_WIN32)
        std::system(("start " + outputImageName).c_str());
#elif defined(__APPLE__)
        std::system(("open " + outputImageName).c_str());
#else
        std::system(("xdg-open " + outputImageName).c_str());
#endif
    }
    else {
        std::cerr << "Ошибка генерации! Убедитесь, что Graphviz установлен и добавлен в PATH." << std::endl;
    }

    return 0;
}