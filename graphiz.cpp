#include <iostream>
#include <fstream>
#include <cstdlib>
#include <memory>
#include <string>
#include <array>
#include <vector>
#include <queue>
#include <set>
#include <algorithm>   
#include <clocale>     

std::vector<std::string> get_dependencies(const std::string& package) {
    std::vector<std::string> deps;
    
    std::string cmd = "python qwert.py \"" + package + "\"";

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
        if (!line.empty()) deps.push_back(line);
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

    std::cout << "Строим граф зависимостей для " << start_package << "...\n";

    size_t processed = 0;
    while (!queue.empty()) {
        std::string current = queue.front();
        queue.pop();
        ++processed;

        std::cout << "[" << processed << "] Обработка: " << current << "\n";

        auto direct_deps = get_dependencies(current);
        for (const auto& dep : direct_deps) {
            edges.push_back({ current, dep });
            if (visited.insert(dep).second) {   // insert вернёт true, если элемента не было
                queue.push(dep);
            }
        }
    }

    std::cout << "Всего пакетов: " << visited.size()
        << ", рёбер: " << edges.size() << "\n";

    std::ofstream outFile("deps_graph.dot");
    if (!outFile.is_open()) {
        std::cerr << "Не удалось создать файл .dot!\n";
        return 1;
    }

    outFile << "digraph Dependencies {\n"
        << "    rankdir=LR;\n"
        << "    node [shape=box, style=\"filled,rounded\", color=\"#1f77b4\","
        " fillcolor=\"#e3f2fd\", fontname=\"Arial\", fontsize=11];\n"
        << "    edge [color=\"#708090\", penwidth=1.5, arrowsize=0.8];\n\n";

    outFile << "    \"" << start_package
        << "\" [fillcolor=\"#ff7f0e\", fontcolor=white, style=filled, fontsize=13];\n\n";

    for (const auto& e : edges)
        outFile << "    \"" << e.first << "\" -> \"" << e.second << "\";\n";

    outFile << "}\n";
    outFile.close();

    if (std::system("dot -Tpng deps_graph.dot -o deps_graph.png") == 0) {
        std::cout << "Граф сохранен в deps_graph.png\n";
#if defined(_WIN32)
        std::system("start deps_graph.png");
#endif
    }
    else {
        std::cerr << "Ошибка Graphviz!\n";
    }
    return 0;
}