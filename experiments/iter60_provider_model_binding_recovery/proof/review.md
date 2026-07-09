# Iteration 60 Review

`iter59` blocked because the selected provider model was called in a location where Vertex returned
a model-not-found-or-access-denied response. `iter60` changed only the local recovered model binding
by setting `vertex_location` to `global`, matching the earlier successful Vertex access probe.

The gate did not execute either BattleSnake row. It did not execute excluded pairs, use GPU, start a
cloud runner, modify Sentinel-named resources, or claim benchmark/model/protocol-effect results.
