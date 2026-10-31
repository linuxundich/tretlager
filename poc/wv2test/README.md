# WebView2 test under Wine

Small C# programs that test WebView2 separately from the Zwift launcher (T2, 2026-10-29).
Built with the `csc.exe` from the winetricks .NET 4.8 in the prefix, against the NuGet package
`Microsoft.Web.WebView2` 1.0.4314.35 (`lib/net462`, `runtimes/win-x64/native/WebView2Loader.dll`).

    F='C:\windows\Microsoft.NET\Framework64\v4.0.30319'
    wine "$F\csc.exe" /target:winexe /platform:x64 /out:WV2Test.exe \
      /r:Microsoft.Web.WebView2.Core.dll /r:Microsoft.Web.WebView2.WinForms.dll \
      /r:System.Windows.Forms.dll WV2Test.cs
    wine "$F\csc.exe" /target:winexe /platform:x64 /out:WV2Wpf.exe \
      /r:Microsoft.Web.WebView2.Core.dll /r:Microsoft.Web.WebView2.Wpf.dll \
      /r:"$F\WPF\PresentationFramework.dll" /r:"$F\WPF\PresentationCore.dll" \
      /r:"$F\WPF\WindowsBase.dll" /r:System.Xaml.dll WV2Wpf.cs

`WV2Wpf.exe hwnd` uses the classic WPF control `WebView2`, `WV2Wpf.exe comp` uses the
`WebView2CompositionControl` of launcher 1.2.
