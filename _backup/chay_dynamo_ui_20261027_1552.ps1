# Mở Revit riêng bằng journal (đã mở Dynamo có giao diện + graph), tự bấm Run, chờ file kết quả rồi đóng phiên.
param([string]$Journal, [string]$FileXong, [int]$ChoToiDa = 900)
Add-Type -AssemblyName UIAutomationClient,UIAutomationTypes
$A=[System.Windows.Automation.AutomationElement]
$p=Start-Process "C:\Program Files\Autodesk\Revit 2027\Revit.exe" -ArgumentList "`"$Journal`"" -WorkingDirectory (Split-Path $Journal) -PassThru
"PID $($p.Id)"
$c=New-Object System.Windows.Automation.PropertyCondition($A::ProcessIdProperty,$p.Id)
$b=$null; $t0=Get-Date
while(-not $b -and ((Get-Date)-$t0).TotalSeconds -lt $ChoToiDa){ Start-Sleep 5
  $rv=$A::RootElement.FindFirst([System.Windows.Automation.TreeScope]::Children,$c)
  if($rv){ $dw=$rv.FindFirst([System.Windows.Automation.TreeScope]::Children,(New-Object System.Windows.Automation.PropertyCondition($A::NameProperty,'Dynamo')))
    if($dw){ $b=$dw.FindFirst([System.Windows.Automation.TreeScope]::Descendants,(New-Object System.Windows.Automation.PropertyCondition($A::AutomationIdProperty,'RunButton'))) } } }
if(-not $b){ "KHONG THAY NUT RUN"; exit 1 }
"Dynamo san sang sau $([int]((Get-Date)-$t0).TotalSeconds)s"; Start-Sleep 5
$b.GetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern).Invoke()
$t1=Get-Date
while(((Get-Date)-$t1).TotalSeconds -lt $ChoToiDa){ Start-Sleep 5
  $t=$dw.FindFirst([System.Windows.Automation.TreeScope]::Descendants,(New-Object System.Windows.Automation.PropertyCondition($A::AutomationIdProperty,'runNotificationTextBlock')))
  if($t -and $t.Current.Name -match 'completed|Run completed|hoàn' -and (Test-Path $FileXong)){ break } }
"Trang thai: $($t.Current.Name) sau $([int]((Get-Date)-$t1).TotalSeconds)s"
Start-Sleep 10
Stop-Process -Id $p.Id -Force
"DA DONG PHIEN"
