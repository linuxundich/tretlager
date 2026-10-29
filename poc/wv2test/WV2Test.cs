using System; using System.IO; using System.Threading.Tasks; using System.Windows.Forms;
using Microsoft.Web.WebView2.Core; using Microsoft.Web.WebView2.WinForms;
class P {
  static StreamWriter log;
  static void L(string s){ var l=DateTime.Now.ToString("HH:mm:ss.fff")+" "+s; Console.WriteLine(l); log.WriteLine(l); log.Flush(); }
  [STAThread] static void Main(string[] a){
    log=new StreamWriter("wv2test.log",false);
    string url = a.Length>0 ? a[0] : "https://example.com/";
    try { L("BrowserVersion: "+CoreWebView2Environment.GetAvailableBrowserVersionString(Environment.GetEnvironmentVariable("WEBVIEW2_BROWSER_EXECUTABLE_FOLDER"))); }
    catch(Exception e){ L("GetAvailableBrowserVersionString FAIL "+e.GetType().Name+" 0x"+e.HResult.ToString("X8")+" "+e.Message); }
    var f=new Form(){Text="WV2Test",Width=900,Height=700};
    var w=new WebView2(){Dock=DockStyle.Fill}; f.Controls.Add(w);
    w.CoreWebView2InitializationCompleted+=(s,e)=>{
      if(e.IsSuccess){ L("Init OK, process "+w.CoreWebView2.BrowserProcessId); w.CoreWebView2.Navigate(url); }
      else L("Init FAIL "+e.InitializationException.GetType().Name+" 0x"+e.InitializationException.HResult.ToString("X8")+" "+e.InitializationException.Message);
    };
    w.NavigationCompleted+=(s,e)=>L("NavigationCompleted success="+e.IsSuccess+" status="+e.WebErrorStatus+" title="+w.CoreWebView2.DocumentTitle);
    f.Shown+=async(s,e)=>{
      L("Form shown, creating environment");
      try { var env=await CoreWebView2Environment.CreateAsync(null, Path.Combine(Path.GetTempPath(),"wv2test-data"));
            L("Environment OK "+env.BrowserVersionString); await w.EnsureCoreWebView2Async(env); L("EnsureCoreWebView2Async returned"); }
      catch(Exception ex){ L("EXC "+ex.GetType().Name+" 0x"+ex.HResult.ToString("X8")+" "+ex.Message); }
    };
    var t=new Timer(){Interval=45000}; t.Tick+=(s,e)=>{L("timeout, exit"); f.Close();}; t.Start();
    Application.Run(f); L("end");
  }
}
