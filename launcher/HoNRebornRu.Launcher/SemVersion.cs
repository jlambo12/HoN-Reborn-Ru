namespace HoNRebornRu.Launcher;

internal sealed class SemVersion : IComparable<SemVersion>
{
    private readonly int[] _numbers;
    private readonly string[] _prerelease;

    private SemVersion(int[] numbers, string[] prerelease)
    {
        _numbers = numbers;
        _prerelease = prerelease;
    }

    public static bool TryParse(string? value, out SemVersion? version)
    {
        version = null;
        if (string.IsNullOrWhiteSpace(value)) return false;
        var clean = value.Trim().TrimStart('v', 'V').Split('+', 2)[0];
        var parts = clean.Split('-', 2);
        var numeric = parts[0].Split('.');
        if (numeric.Length is < 2 or > 4) return false;
        var numbers = new int[Math.Max(3, numeric.Length)];
        for (var index = 0; index < numeric.Length; index++)
        {
            if (!int.TryParse(numeric[index], out numbers[index]) || numbers[index] < 0) return false;
        }
        var prerelease = parts.Length == 2 ? parts[1].Split('.') : [];
        version = new SemVersion(numbers, prerelease);
        return true;
    }

    public int CompareTo(SemVersion? other)
    {
        if (other is null) return 1;
        for (var index = 0; index < Math.Max(_numbers.Length, other._numbers.Length); index++)
        {
            var left = index < _numbers.Length ? _numbers[index] : 0;
            var right = index < other._numbers.Length ? other._numbers[index] : 0;
            var compared = left.CompareTo(right);
            if (compared != 0) return compared;
        }
        if (_prerelease.Length == 0 && other._prerelease.Length == 0) return 0;
        if (_prerelease.Length == 0) return 1;
        if (other._prerelease.Length == 0) return -1;
        for (var index = 0; index < Math.Max(_prerelease.Length, other._prerelease.Length); index++)
        {
            if (index >= _prerelease.Length) return -1;
            if (index >= other._prerelease.Length) return 1;
            var leftNumeric = int.TryParse(_prerelease[index], out var leftNumber);
            var rightNumeric = int.TryParse(other._prerelease[index], out var rightNumber);
            int compared;
            if (leftNumeric && rightNumeric) compared = leftNumber.CompareTo(rightNumber);
            else if (leftNumeric) compared = -1;
            else if (rightNumeric) compared = 1;
            else compared = string.Compare(_prerelease[index], other._prerelease[index], StringComparison.OrdinalIgnoreCase);
            if (compared != 0) return compared;
        }
        return 0;
    }
}
