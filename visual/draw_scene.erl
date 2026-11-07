%% draw_scene.erl — 6502 program that emits a richer GPU command stream
%% including sprite define + draw and an immediate blit.
%%
%% Assemble and run with the Stage-1 runtime:
%%
%%   {ok, Bin, _} = mv_asm:assemble(terms(), 16#0200),
%%   {ok, _Out, M} = mv6502:run_binary(Bin, 16#0200, 100000),
%%   Queue = mv6502:gpu_queue(M).
%%
%% Then feed Queue to visual/queue_renderer.py.

-module(draw_scene).
-export([terms/0]).

terms() ->
    [
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

%% 8x8 diamond sprite (palette indices, 0 = transparent)
sprite() ->
    [0,0,0,1,1,0,0,0,
     0,0,1,4,4,1,0,0,
     0,1,4,2,2,4,1,0,
     1,4,2,7,7,2,4,1,
     1,4,2,7,7,2,4,1,
     0,1,4,2,2,4,1,0,
     0,0,1,4,4,1,0,0,
     0,0,0,1,1,0,0,0].

table() ->
    [
     %% SET_COLOR ink, CLEAR
     16#01, 16#0E, 16#10, 16#0E,
     16#04,
     %% brass frame
     16#01, 16#D4, 16#A2, 16#4C,
     16#09, 20, 20, 280, 200,
     %% inner panel
     16#01, 16#17, 16#1C, 16#17,
     16#02, 30, 40, 260, 160,
     %% neon circles
     16#01, 16#D4, 16#A2, 16#4C,
     16#08, 80, 100, 18,
     16#07, 240, 100, 22,
     %% cross
     16#0A, 40, 130, 240,
     16#0B, 160, 50, 140,
     %% DEFINE_SPRITE id=1 8x8
     16#0D, 1, 8, 8
    ] ++ sprite() ++
    [
     %% DRAW_SPRITE in a few places
     16#0E, 1, 50, 70,
     16#0E, 1, 70, 90,
     16#0E, 1, 200, 80,
     16#0E, 1, 220, 100,
     %% BLIT a 16x4 bar
     16#0F, 140, 140, 16, 4
    ] ++ lists:flatten(lists:duplicate(16, [1,1,4,4])) ++
    [
     %% title
     16#01, 16#E8, 16#E6, 16#DC,
     16#05, 50, 160, 16
    ] ++ "SOVEREIGN CIRCUIT" ++
    [16#05, 110, 175, 6] ++ "FABRIC" ++
    [16#FF].
