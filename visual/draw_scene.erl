%% draw_scene.erl — 6502 program that emits a 4-frame animation
%% plus rising tones and a short noise burst.
%%
%% Assemble and run:
%%   {ok, Bin, _} = mv_asm:assemble(terms(), 16#0200),
%%   {ok, _Out, M} = mv6502:run_binary(Bin, 16#0200, 100000),
%%   Queue = mv6502:gpu_queue(M).

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

sprite() ->
    [0,0,0,1,1,0,0,0,
     0,0,1,4,4,1,0,0,
     0,1,4,2,2,4,1,0,
     1,4,2,7,7,2,4,1,
     1,4,2,7,7,2,4,1,
     0,1,4,2,2,4,1,0,
     0,0,1,4,4,1,0,0,
     0,0,0,1,1,0,0,0].

%% One frame: clear, frame, panel, pulsing circle, moving sprite, optional title, tone, PRESENT.
frame(N, SpriteX) ->
    Base = [
     16#01, 16#0E, 16#10, 16#0E,
     16#04,
     16#01, 16#D4, 16#A2, 16#4C,
     16#09, 20, 20, 280, 200,
     16#01, 16#17, 16#1C, 16#17,
     16#02, 30, 40, 260, 160,
     16#01, 16#D4, 16#A2, 16#4C,
     16#08, 80, 100, 14 + N * 2,
     16#0D, 1, 8, 8
    ] ++ sprite() ++
    [16#0E, 1, SpriteX, 90],
    Title = case N of
        3 ->
            [16#01, 16#E8, 16#E6, 16#DC,
             16#05, 50, 160, 16] ++ "SOVEREIGN CIRCUIT";
        _ -> []
    end,
    Freq = 220 + N * 110,
    Tone = [16#10, Freq band 16#FF, (Freq bsr 8) band 16#FF, 120],
    Noise = case N of
        2 -> [16#11, 40];
        _ -> []
    end,
    Base ++ Title ++ Tone ++ Noise ++ [16#FF].

table() ->
    lists:flatten([frame(N, 40 + N * 40) || N <- [0,1,2,3]]).
