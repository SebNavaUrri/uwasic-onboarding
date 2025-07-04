/*
 * Copyright (c) 2024 Sebastian Nava Urribarri
 * SPDX-License-Identifier: Apache-2.0
 */

`default_nettype none

module spi_peripheral (
    input  wire cs,      // chip select
    input wire sclk,      // source clock
    input wire copi, // master out slave in
    input  wire rst,    // reset_n - low to reset
    input wire clk, // system clock
  //  output reg [15:0] out, // final output

    output reg [7:0] en_reg_out_7_0,
    output reg [7:0] en_reg_out_15_8,
    output reg [7:0] en_reg_pwm_7_0,
    output reg [7:0] en_reg_pwm_15_8,
    output reg [7:0] pwm_duty_cycle

    //already in here so must be important
);

   reg transaction_ready = 1'b0;
   reg [2:0] sclk_synchronised; 
   reg [2:0] cs_syncrhonised;
   reg[2:0] copi_synchronised;
    // because we need both the oldest and second oldest values

    //reg read_or_write;     // one for read / write
    reg [6:0] address_bits;     // one for address
    reg [7:0] information_bits;     // one for information
   // reg [15:0] all_bits;     // one register for everything
    reg [15:0] counter;

    wire cs_falls = (cs_syncrhonised[1] == 1'b1 ) & (cs_syncrhonised[2] == 1'b0);
    //wire cs_rises = (cs_syncrhonised[1] == 0'b1 ) & (cs_syncrhonised[2] == 1'b1);

    wire sclk_rising  = (sclk_synchronised[2:1] == 2'b01);
   // wire sclk_falling = (sclk_synchronised[2:1] == 2'b10);
// block for signal scyhrnoisation

always @(posedge clk or negedge rst) 
begin
    if (!rst) begin
        sclk_synchronised <= 3'b000;
        cs_syncrhonised   <= 3'b000;
        copi_synchronised <= 3'b111;
    end else begin
        sclk_synchronised <= {sclk_synchronised[1:0], sclk};
        cs_syncrhonised   <= {cs_syncrhonised[1:0], cs};
        copi_synchronised <= {copi_synchronised[1:0], copi};
    end
end

always@(posedge clk or negedge rst)
begin
    if (!rst)
    begin
      //  read_or_write <= 1'b0;
        address_bits <= 7'b0000000;
        information_bits <= 8'h00;
       // all_bits <= 16'h0000;
        counter <= 0;
        transaction_ready <= 1'b0;
        en_reg_out_7_0 <= 8'h00;
        en_reg_out_15_8 <= 8'h00;
        en_reg_pwm_7_0  <= 8'h00;
        en_reg_pwm_15_8 <= 8'h00;
        pwm_duty_cycle <= 8'h00;
    end

    // signal sychnornisation portion
    else 
    begin

    if (cs_falls) // get rid of everything in the register to get ready for next time
        begin
       // read_or_write <= 1'b0;   
        address_bits <= 7'b0;   
        information_bits <= 8'b0;   
       // all_bits <= 16'b0;    
        counter <=0;
        end
    else if((cs_syncrhonised[2] == 1'b0) & (!transaction_ready))
    begin
        if(sclk_rising)
        begin
            if (counter == 0)
            begin
           // read_or_write <= copi_synchronised[2]; // take in the first bit
            end 
            else if ((counter > 1) & (counter < 8))
            begin
                address_bits <= {address_bits[5:0], copi_synchronised[2]}; // take address, shuffling everything over
            end
            else if (counter < 16)
            begin
                information_bits <= {information_bits[6:0], copi_synchronised[2]}; // take info, shuffling everything over
            end
        counter <= counter + 1; // increment coutner until we get all bits we need
        end
        if (counter == 15)
        begin
            transaction_ready <= 1'b1;
        end 
// transaction stuff
    if ((counter == 16)) 
    begin
        case(address_bits)
        7'b0000000: en_reg_out_7_0<=information_bits;
        7'b0000001: en_reg_out_15_8<=information_bits;
        7'b0000010: en_reg_pwm_7_0<=information_bits;
        7'b0000011: en_reg_pwm_15_8<=information_bits;
        7'b0000100: pwm_duty_cycle<=information_bits;
        default: ;
        endcase
    transaction_ready <= 1'b0;
    end
    end
end 
end
endmodule
