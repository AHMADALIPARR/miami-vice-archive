%% draw_scene.erl — 6502 program that emits a richer GPU command stream.
%%
%% Assemble and run with the Stage-1 runtime:
%%
%%   {ok, Bin, _} = mv_asm:assemble(terms(), 16#0200),
%%   {ok, _Out, M} = mv6502:run_binary(Bin, 16#0200, 100000),
%%   Queue = mv6502:gpu_queue(M).
%%
%% Then feed Queue to visual/queue_renderer.py (as [[addr,byte],...]).
%%
%% The program copies a byte table to consecutive addresses starting at
%% $C100. Every STA to that window is captured by the runtime in order.

-module(draw_scene).
-export([terms/0]).

%% terms/0 -> list of mv_asm terms. Origin $0200 (banked program window).
terms() ->
    [
     %% copy table to queue window
     {ldx, {imm, 0}},
     {label, copy},
     {lda, {abx, data}},
     {sta, {abx, 16#C100}},
     {inx, imp},
     {cpx, {imm, table_len()}},
     {bne, {rel, copy}},
     {brk, imp},

     {label, data}
     | [{bytes, [B]} || B <- table()]
    ].

table_len() -> length(table()).

%% The command stream the 6502 writes (same bytes the Python sample emits).
table() ->
    [
     %% SET_COLOR ink, CLEAR
     16#01, 16#0E, 16#10, 16#0E,
     16#04,
     %% brass frame
     16#01, 16#D4, 16#A2, 16#4C,
     16#09, 20, 20, 280, 200,          % RECT_OUTLINE
     %% inner panel
     16#01, 16#17, 16#1C, 16#17,
     16#02, 30, 40, 260, 160,          % FILL_RECT
     %% neon circles
     16#01, 16#D4, 16#A2, 16#4C,
     16#08, 80, 100, 18,               % FILL_CIRCLE
     16#07, 240, 100, 22,              % CIRCLE
     %% cross lines
     16#0A, 40, 130, 240,              % HLINE
     16#0B, 160, 50, 140,              % VLINE
     %% title
     16#01, 16#E8, 16#E6, 16#DC,
     16#05, 50, 160, 16                % TEXT "SOVEREIGN CIRCUIT"
     | "SOVEREIGN CIRCUIT" ++
     [
      16#05, 110, 175, 6               % TEXT "FABRIC"
     | "FABRIC" ] ++
     [
      16#FF                            % PRESENT
     ]
    ].
