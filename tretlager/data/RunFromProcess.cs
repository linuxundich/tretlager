// Starts a program as a child process of another process (PROC_THREAD_ATTRIBUTE_PARENT_PROCESS).
// Usage: RunFromProcess.exe <parent PID> <program> [arguments ...]
// Same job as runfromprocess-rs (netbrain/zwift); written in C# here so that csc.exe from the
// .NET 4.8 prefix is enough.
using System;
using System.ComponentModel;
using System.Runtime.InteropServices;
using System.Text;

class RunFromProcess
{
    const uint EXTENDED_STARTUPINFO_PRESENT = 0x00080000;
    const uint CREATE_UNICODE_ENVIRONMENT = 0x00000400;
    const uint PROCESS_CREATE_PROCESS = 0x0080;
    static readonly IntPtr PROC_THREAD_ATTRIBUTE_PARENT_PROCESS = (IntPtr)0x00020000;

    [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
    struct STARTUPINFO
    {
        public int cb; public string lpReserved, lpDesktop, lpTitle;
        public int dwX, dwY, dwXSize, dwYSize, dwXCountChars, dwYCountChars, dwFillAttribute, dwFlags;
        public short wShowWindow, cbReserved2; public IntPtr lpReserved2, hStdInput, hStdOutput, hStdError;
    }
    [StructLayout(LayoutKind.Sequential)]
    struct STARTUPINFOEX { public STARTUPINFO StartupInfo; public IntPtr lpAttributeList; }
    [StructLayout(LayoutKind.Sequential)]
    struct PROCESS_INFORMATION { public IntPtr hProcess, hThread; public int dwProcessId, dwThreadId; }

    [DllImport("kernel32.dll", SetLastError = true)]
    static extern IntPtr OpenProcess(uint access, bool inherit, int pid);
    [DllImport("kernel32.dll", SetLastError = true)]
    static extern bool InitializeProcThreadAttributeList(IntPtr list, int count, int flags, ref IntPtr size);
    [DllImport("kernel32.dll", SetLastError = true)]
    static extern bool UpdateProcThreadAttribute(IntPtr list, uint flags, IntPtr attr, IntPtr value, IntPtr size, IntPtr prev, IntPtr retSize);
    [DllImport("kernel32.dll")]
    static extern void DeleteProcThreadAttributeList(IntPtr list);
    [DllImport("kernel32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
    static extern bool CreateProcess(string app, StringBuilder cmd, IntPtr pa, IntPtr ta, bool inherit, uint flags,
        IntPtr env, string dir, ref STARTUPINFOEX si, out PROCESS_INFORMATION pi);
    [DllImport("kernel32.dll")]
    static extern bool CloseHandle(IntPtr h);

    static string Quote(string a)
    {
        if (a.Length > 0 && a.IndexOfAny(new[] { ' ', '\t', '"' }) < 0) return a;
        return "\"" + a.Replace("\\\"", "\\\\\"").Replace("\"", "\\\"") + "\"";
    }

    // "--token=@C:\\path\\file" is replaced by the file's content. This keeps the token out of the
    // command line of the calling Linux process (process list, error messages).
    static string ExpandFileArg(string a)
    {
        int at = a.IndexOf("=@", StringComparison.Ordinal);
        if (at < 0) return a;
        string path = a.Substring(at + 2);
        return a.Substring(0, at + 1) + System.IO.File.ReadAllText(path).Trim();
    }

    static int Main(string[] args)
    {
        if (args.Length < 2) { Console.Error.WriteLine("Usage: RunFromProcess.exe <PID> <program> [arguments]"); return 2; }
        int pid = int.Parse(args[0]);
        var cmd = new StringBuilder(Quote(args[1]));
        for (int i = 2; i < args.Length; i++) cmd.Append(' ').Append(Quote(ExpandFileArg(args[i])));

        IntPtr parent = OpenProcess(PROCESS_CREATE_PROCESS, false, pid);
        if (parent == IntPtr.Zero) { Console.Error.WriteLine("OpenProcess: " + new Win32Exception().Message); return 1; }

        IntPtr size = IntPtr.Zero;
        InitializeProcThreadAttributeList(IntPtr.Zero, 1, 0, ref size);
        IntPtr list = Marshal.AllocHGlobal(size);
        IntPtr parentBox = Marshal.AllocHGlobal(IntPtr.Size);
        try
        {
            if (!InitializeProcThreadAttributeList(list, 1, 0, ref size)) throw new Win32Exception();
            Marshal.WriteIntPtr(parentBox, parent);
            if (!UpdateProcThreadAttribute(list, 0, PROC_THREAD_ATTRIBUTE_PARENT_PROCESS, parentBox, (IntPtr)IntPtr.Size, IntPtr.Zero, IntPtr.Zero))
                throw new Win32Exception();
            var si = new STARTUPINFOEX();
            si.StartupInfo.cb = Marshal.SizeOf(typeof(STARTUPINFOEX));
            si.lpAttributeList = list;
            PROCESS_INFORMATION pi;
            if (!CreateProcess(null, cmd, IntPtr.Zero, IntPtr.Zero, false, EXTENDED_STARTUPINFO_PRESENT | CREATE_UNICODE_ENVIRONMENT,
                    IntPtr.Zero, Environment.CurrentDirectory, ref si, out pi))
                throw new Win32Exception();
            Console.WriteLine("started, PID " + pi.dwProcessId + " under parent PID " + pid);
            CloseHandle(pi.hThread); CloseHandle(pi.hProcess);
            return 0;
        }
        catch (Win32Exception e) { Console.Error.WriteLine("Error: " + e.Message); return 1; }
        finally
        {
            DeleteProcThreadAttributeList(list);
            Marshal.FreeHGlobal(list); Marshal.FreeHGlobal(parentBox);
            CloseHandle(parent);
        }
    }
}
