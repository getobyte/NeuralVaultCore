# NeuralVaultCore — PowerShell shell hook
# Add to $PROFILE: . "C:\path\to\NeuralVaultCore\hooks\powershell_hook.ps1"

$script:NVC_DIR = Split-Path -Parent (Split-Path -Parent $PSCommandPath)
$script:NVC_LAST_CMD = ""

Set-PSReadLineKeyHandler -Key Enter -ScriptBlock {
    # Get the current command line
    $line = $null
    [Microsoft.PowerShell.PSConsoleReadLine]::GetBufferState([ref]$line, [ref]$null)

    if ($line -and $line.Trim().Length -ge 5 -and $line -ne $script:NVC_LAST_CMD) {
        $script:NVC_LAST_CMD = $line
        $nvcDir = $script:NVC_DIR
        # Run capture in background job
        Start-Job -ScriptBlock {
            param($dir, $cmd)
            & python "$dir\core\shell_capture.py" $cmd
        } -ArgumentList $nvcDir, $line | Out-Null
    }

    # Execute the original Enter behavior
    [Microsoft.PowerShell.PSConsoleReadLine]::AcceptLine()
}
