// Testbench for alu_top module
`timescale 1ns/1ps

module alu_tb;

    logic        clk;
    logic        rst_n;
    logic [3:0]  opcode;
    logic [7:0]  a;
    logic [7:0]  b;
    logic [7:0]  result;
    logic        zero;
    logic        overflow;

    alu_top dut (
        .clk(clk),
        .rst_n(rst_n),
        .opcode(opcode),
        .a(a),
        .b(b),
        .result(result),
        .zero(zero),
        .overflow(overflow)
    );

    // Clock generator (100MHz)
    always #5 clk = ~clk;

    initial begin
        clk = 0;
        rst_n = 0;
        opcode = 0;
        a = 8'h00;
        b = 8'h00;

        #20 rst_n = 1;

        // Test ADD
        @(posedge clk);
        opcode = 4'b0000;
        a = 8'd10;
        b = 8'd25;

        // Test SUB
        @(posedge clk);
        opcode = 4'b0001;
        a = 8'd50;
        b = 8'd20;

        // Test AND
        @(posedge clk);
        opcode = 4'b0010;
        a = 8'hAA;
        b = 8'h55;

        #50;
        $finish;
    end

endmodule
