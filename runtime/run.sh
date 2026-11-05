#!/bin/sh
# run.sh PROGRAM.bin [ORG_HEX] [BUDGET] — run a 6502 binary on the
# banked archive map and write its output bytes to stdout. The halt
# status goes to stderr. Exit 0 on a clean BRK, 1 otherwise.
set -e
cd "$(dirname "$0")"
[ -d ebin ] || bash build.sh
exec erl -noshell -pa ebin -eval '
  [Prog, OrgHex, BudgetS] =
    case init:get_plain_arguments() of
      [P] -> [P, "8000", "1000000"];
      [P, O] -> [P, O, "1000000"];
      [P, O, B] -> [P, O, B]
    end,
  {ok, Bin} = file:read_file(Prog),
  Org = list_to_integer(OrgHex, 16),
  Budget = list_to_integer(BudgetS),
  case mv6502:run_binary(Bin, Org, Budget) of
    {ok, Out, M} ->
      io:format("~s", [Out]),
      #{steps := Steps} = mv6502:registers(M),
      io:format(standard_error, "halted: brk, steps=~p~n", [Steps]),
      halt(0);
    {error, Reason, Out, M} ->
      io:format("~s", [Out]),
      #{steps := Steps} = mv6502:registers(M),
      io:format(standard_error, "halted: ~p, steps=~p~n", [Reason, Steps]),
      halt(1)
  end.' -- "$@"
