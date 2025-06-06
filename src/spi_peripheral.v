/*
 * Copyright (c) 2024 Sebastian Nava Urribarri
 * SPDX-License-Identifier: Apache-2.0
 */

`default_nettype none
module counter (  input counter_clock, input rstn, output reg[15:0] out);    

  always @ (posedge counter_clock) begin
    if (! rstn)
      out <= 0;
    else
      out <= out + 1;
  end

endmodule

module spi_peripheral (
    input  wire cs,      // chip select
    input wire sclk,      // source clock
    input wire copi, // master out slave in
    input  wire rst,    // reset_n - low to reset
    input wire clk, // system clock
    output reg [15:0] out, // final output

    output reg [7:0] en_reg_out_7_0,
    output reg [7:0] en_reg_out_15_8,
    output reg [7:0] en_reg_pwm_7_0,
    output reg [7:0] en_reg_pwm_15_8,
    output reg [7:0] pwm_duty_cycle

    //already in here so must be important
);

   parameter transcation_ready = 0'b0;
   parameter transaction_complete = 0'b0;
   reg [2:0] sclk_synchronised; 
   reg [2:0] cs_syncrhonised;
   reg[2:0] copi_synchronised;
    // because we need both the oldest and second oldest values

    reg [0:0] read_or_write;     // one for read / write
    reg [6:0] adress_bits;     // one for adress
    reg [7:0] information_bits;     // one for information
    reg [15:0] all_bits;     // one register for everything

// block for signal scyhrnoisation
    always@(posedge sclk or negedge sclk)
    if (!rst)
    begin
        en_reg_out_7_0 <= 8'h00;
        en_reg_out_15_8 <= 8'h00;
        en_reg_pwm_7_0 <= 8'h00;
        en_reg_pwm_15_8 <= 8'h00;
        pwm_duty_cycle <= 8'h00;

        sclk_synchronised <= 2'b00;
        cs_syncrhonised <= 2'b00;
        copi_synchronised <= 2'b11;

        transaction_ready <= 1'b0; 
        transaction_complete <= 1'b1;
    end

    // signal sychnornisation portion
    begin
        sclk_synchronised <= {sclk_synchronised[1:0], sclk}; // second oldest and oldest values
        cs_syncrhonised <= {cs_syncrhonised[1:0], cs};
        copi_synchronised <= {copi_synchronised[1:0], copi};
     end

// block for transport 

    always@(posedge sclk or negedge sclk)
    begin
// if not reset, activate signal clock and select a preipheral by setting chip selec to 0
// after transcation is finished, chip select returns to 1
// signal slock sclk determines when data bits are sent and read
// peripheral can confugyre if its rising edge or falling edge
//  sample copi, sclk and nCS at every rising edge of the internal clk
// transition identification positive edge is (2nd oldest is high) and (1st oldest is low)
// negative edge = (2nd oldest = low) and (1st oldest = high)
    if (!rst)
    begin
        en_reg_out_7_0 <= 8'h00;
        en_reg_out_15_8 <= 8'h00;
        en_reg_pwm_7_0 <= 8'h00;
        en_reg_pwm_15_8 <= 8'h00;
        pwm_duty_cycle <= 8'h00;

        sclk_synchronised <= 2'b00;
        cs_syncrhonised <= 2'b00;
        copi_synchronised <= 2'b11;

        transaction_ready <= 1'b0; 
        transaction_complete <= 1'b1;
    end
    else if((sclk_synchronised[1] & 1'b0 ) & (sclk_synchronised[0] ^ 0'b0))
    begin

    end
    else if ((sclk_synchronised[1] ^ 0'b0 ) & (sclk_synchronised[0] & 1'b0))
    begin
        
    end

    end

// transaction stuff
    if (transcation_ready) 
    begin
        if(all_bits[15])
        begin
        
        end

    end

endmodule
