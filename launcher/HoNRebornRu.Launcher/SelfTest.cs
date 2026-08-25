namespace HoNRebornRu.Launcher;

internal static class SelfTest
{
    public static int Run()
    {
        var failures = new List<string>();
        if (!SemVersion.TryParse("0.1.0-beta.2", out var beta2)) failures.Add("parse beta2");
        if (!SemVersion.TryParse("0.1.0-beta.10", out var beta10)) failures.Add("parse beta10");
        if (!SemVersion.TryParse("0.1.0", out var stable)) failures.Add("parse stable");
        if (beta2 is null || beta10 is null || beta2.CompareTo(beta10) >= 0) failures.Add("beta numeric ordering");
        if (beta10 is null || stable is null || beta10.CompareTo(stable) >= 0) failures.Add("stable ordering");
        if (failures.Count == 0)
        {
            Console.WriteLine("PASS: launcher self-test");
            return 0;
        }
        Console.Error.WriteLine("FAIL: " + string.Join(", ", failures));
        return 1;
    }
}
