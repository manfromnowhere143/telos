# Iter243 preregistration-record correction

Status: **invalid preregistration record corrected prospectively**.

The safe-path amendment records a nonexistent hypothesis commit at line 6.
The exact immutable hypothesis commit is
`0b49c1ff9030c20d8f196101b2677675b9ed71a3`, not the value written there.

The amendment also says it preceded every Iter243 diagnostic implementation.
That statement is true only of the reconstructed candidate DAG. It is not true
of the complete operator chronology: diagnostic code and local testing existed
on an abandoned local history before the additive amendment was created. An
earlier local commit, `08342d7b34ee10d62d38fe575a83b7d470915ad7`, did add the
`safe_path` requirement before the main trust-policy implementation and before
any hosted outcome, but it did so by modifying the immutable hypothesis in
place and therefore was not a valid amendment.

This correction does not rewrite either record or retroactively validate the
amendment. Iter243 preregistration integrity is `invalid`. The implemented
four-flag denial remains independently testable engineering behavior, and the
hosted world-writable-executable result remains a retained failure.
