$taskName = "DailyFormSubmission"
$batPath = "C:\Users\akhil\Documents\AI Agents\Daily report workflow\run_form.bat"

$action = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c `"$batPath`""

$triggers = @(
    $(New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday -At "11:00PM"),
    $(New-ScheduledTaskTrigger -Weekly -DaysOfWeek Tuesday -At "11:00PM"),
    $(New-ScheduledTaskTrigger -Weekly -DaysOfWeek Wednesday -At "11:00PM"),
    $(New-ScheduledTaskTrigger -Weekly -DaysOfWeek Thursday -At "11:00PM"),
    $(New-ScheduledTaskTrigger -Weekly -DaysOfWeek Friday -At "11:00PM")
)

$settings = New-ScheduledTaskSettingsSet -ExecutionTimeLimit (New-TimeSpan -Minutes 10) -StartWhenAvailable

$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Highest

$task = New-ScheduledTask -Action $action -Trigger $triggers -Settings $settings -Principal $principal

Register-ScheduledTask -TaskName $taskName -InputObject $task -Force

Write-Host "Scheduled task '$taskName' created successfully."
Get-ScheduledTask -TaskName $taskName | Select-Object TaskName, State
