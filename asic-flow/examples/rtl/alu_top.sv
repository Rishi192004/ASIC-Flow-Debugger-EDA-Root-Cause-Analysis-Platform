// 8-bit Arithmetic Logic Unit (ALU) Top Module
module alu_top (
    input  logic        clk,
    input  logic        rst_n,
    input  logic [3:0]  opcode,
    input  logic [7:0]  a,
    input  logic [7:0]  b,
    output logic [7:0]  result,
    output logic        zero,
    output logic        overflow
);

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            result   <= 8'h00;
            zero     <= 1'b1;
            overflow <= 1'b0;
        end else begin
            case (opcode)
                4'b0000: {overflow, result} <= {1'b0, a} + {1'b0, b}; // ADD
                4'b0001: {overflow, result} <= {1'b0, a} - {1'b0, b}; // SUB
                4'b0010: begin result <= a & b; overflow <= 1'b0; end  // AND
                4'b0011: begin result <= a | b; overflow <= 1'b0; end  // OR
                4'b0100: begin result <= a ^ b; overflow <= 1'b0; end  // XOR
                4'b0101: begin result <= ~a;    overflow <= 1'b0; end  // NOT A
                4'b0110: begin result <= a << 1; overflow <= a[7]; end // SHL
                4'b0111: begin result <= a >> 1; overflow <= 1'b0; end // SHR
                default: begin result <= 8'h00; overflow <= 1'b0; end
            endcase
            zero <= (result == 8'h00);
        end
    end

endmodule
