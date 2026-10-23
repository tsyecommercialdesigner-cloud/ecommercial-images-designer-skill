param(
    [Parameter(Mandatory)][ValidateSet('Read', 'Write')][string]$Operation,
    [Parameter(Mandatory)][string]$LiteralPath
)
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [Text.UTF8Encoding]::new($false)
try {
    if ($Operation -eq 'Read') { [Console]::Write([IO.File]::ReadAllText($LiteralPath)) }
    else { [IO.File]::WriteAllText($LiteralPath, 'WRITE_MUST_BE_DENIED') }
    exit 0
}
catch {
    # MethodInvocationException wraps the real filesystem exception. Emit an
    # ASCII record so localized messages and proxy encoding cannot decide PASS.
    # The base64 field is path data only, never executable command text.
    $cause = $_.Exception.GetBaseException()
    $pathData = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes([IO.Path]::GetFullPath($LiteralPath)))
    [Console]::Error.WriteLine(('SANDBOX_PROBE_ERROR_V1|operation={0}|type={1}|hresult={2}|pathUtf8Base64={3}' -f
        $Operation, $cause.GetType().FullName, $cause.HResult, $pathData))
    [Console]::Error.WriteLine($_.Exception.Message)
    exit 1
}
