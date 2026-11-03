
#include <iostream>
#include <fstream>
#include <cstdlib>
#include <memory>
#include <string>
#include <array>
#include <vector>
#include <queue>
#include <set>

std::vector<std::string> get_dependencies(const std::string& package) {
    std::vector<std::string> deps;
    std::string cmd = "python qwert.py " + package;

#if defined(_WIN32)
    std::unique_ptr<FILE, decltype(&_pclose)> pipe(_popen(cmd.c_str(), "r"), _pclose);
#else
    std::unique_ptr<FILE, decltype(&pclose)> pipe(popen(cmd.c_str(), "r"), pclose);
#endif

    if (!pipe) return deps;

    std::array<char, 128> buffer;
    while (fgets(buffer.data(), buffer.size(), pipe.get()) != nullptr) {
        std::string line(buffer.data());
        line.erase(std::remove(line.begin(), line.end(), '\n'), line.end());
        line.erase(std::remove(line.begin(), line.end(), '\r'), line.end());
        if (!line.empty()) {
            deps.push_back(line);
        }
    }
    return deps;
}

int main() {
    setlocale(LC_ALL, "Russian");

    std::string start_package = "matplotlib";
    std::queue<std::string> queue;
    std::set<std::string> visited;
    std::vector<std::pair<std::string, std::string>> edges;

    queue.push(start_package);
    visited.insert(start_package);

    std::cout << "Строим граф зависимостей для " << start_package << "..." << std::endl;

    while (!queue.empty()) {
        std::string current = queue.front();
        queue.pop();

        std::cout << "Обработка: " << current << std::endl;

        std::vector<std::string> direct_deps = get_dependencies(current);

        for (const std::string& dep : direct_deps) {
            edges.push_back({ current, dep });

            if (visited.find(dep) == visited.end()) {
                visited.insert(dep);
                queue.push(dep);
            }
        }
    }

    std::string dotFileName = "deps_graph.dot";
    std::ofstream outFile(dotFileName);

    if (!outFile.is_open()) {
        std::cerr << "Не удалось создать файл .dot!" << std::endl;
        return 1;
    }

    outFile << "digraph Dependencies {\n"
        << "    rankdir=LR;\n"
        << "    node [shape=box, style=\"filled,rounded\", color=\"#1f77b4\", fillcolor=\"#e3f2fd\", fontname=\"Arial\", fontsize=11];\n"
        << "    edge [color=\"#708090\", penwidth=1.5, arrowsize=0.8];\n\n";

    outFile << "    \"" << start_package << "\" [fillcolor=\"#ff7f0e\", fontcolor=white, style=filled, fontsize=13];\n\n";

    for (const auto& edge : edges) {
        outFile << "    \"" << edge.first << "\" -> \"" << edge.second << "\";\n";
    }

    outFile << "}\n";
    outFile.close();

    std::string graphvizCmd = "dot -Tpng " + dotFileName + " -o deps_graph.png";
    int result = std::system(graphvizCmd.c_str());

    if (result == 0) {
        std::cout << "Граф сохранен в deps_graph.png" << std::endl;
#if defined(_WIN32)
        std::system("start deps_graph.png");
#endif
    }
    else {
        std::cerr << "Ошибка Graphviz!" << std::endl;
    }

    return 0;
}