// Sample C++ testbench for Verilator
#include <iostream>
#include "Vcounter.h"
#include "verilated.h"

int main(int argc, char** argv) {
    Verilated::commandArgs(argc, argv);
    Vcounter* top = new Vcounter;

    top->clk = 0;
    top->rst_n = 0;
    top->en = 0;
    top->eval();

    std::cout << "Testbench initialized successfully." << std::endl;

    delete top;
    return 0;
}
