# Shared research code

These modules are used by more than one experiment family. They define stable
data structures, locate experiment definitions, calculate common measurements,
write immutable run folders, capture environment information, and validate
published evidence.

They do not implement a thesis experiment by themselves. Domain-specific code
belongs in `policy/`, `extraction/`, `datasets/`, `live/`, or `comparisons/`.
