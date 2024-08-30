import numpy as np
from pymclevel import alphaMaterials

try:
    import br
except ImportError:
    raise ImportError("Couldn't find 'br.py', have you put it in the same "
            "filter folder? It can be downloaded from: "
            "github.com/FrostyAceHook/br-filters")
try:
    br.require_version(2, 1)
except AttributeError:
    raise ImportError("Outdated version of 'br.py'. Please download the latest "
            "compatible version from: github.com/FrostyAceHook/br-filters")


displayName = "Line"


inputs = (
    ("Sets the blocks in a straight line between the two selection points.",
            "label"),
    ("Replace:", "string"),
    ("Block:", alphaMaterials.Glowstone),
    br.selector_explain("replace"),
)


def perform(level, box, options):
    replace = br.selector("replace", options["Replace:"])
    bid, bdata = options["Block:"].ID, options["Block:"].blockData

    # Grab the selection blocks, same method as mark sel but without a fallback
    # since otherwise you can't control the direction of the line.
    x1, y1, z1 = editor.selectionTool.bottomLeftPoint
    x2, y2, z2 = editor.selectionTool.topRightPoint

    # Set all the points in a line.
    for x, y, z in iter_line(x1, y1, z1, x2, y2, z2):
        # Create a 3d array of just this block, to use with the standard selector
        # api.
        ids = np.array([[[level.blockAt(x, y, z)]]])
        datas = np.array([[[level.blockDataAt(x, y, z)]]])
        mask = replace.matches(ids, datas)

        # Check if the one block matched.
        if mask[0, 0, 0]:
            level.setBlockAt(x, y, z, bid)
            level.setBlockDataAt(x, y, z, bdata)


    print "Finished lining."
    print "- replace: {}".format(replace)
    print "- block: ({}:{})".format(bid, bdata)
    return



def iter_line(x, y, z, x2, y2, z2):
    # Implementation of Bresenham's line algorithm (3d).
    # https://en.wikipedia.org/wiki/Bresenham%27s_line_algorithm

    dx = abs(x2 - x)
    dy = abs(y2 - y)
    dz = abs(z2 - z)

    ix = 1 if (x2 > x) else -1
    iy = 1 if (y2 > y) else -1
    iz = 1 if (z2 > z) else -1

    # Yield the first point separately.
    points = [(x, y, z)]

    # Find the longest axis and iterate along it.
    if dx == max(dx, dy, dz):
        D1 = (2 * dy) - dx
        D2 = (2 * dz) - dx
        while x != x2:
            x += ix
            if D1 >= 0:
                y += iy
                D1 -= 2 * dx
            if D2 >= 0:
                z += iz
                D2 -= 2 * dx
            D1 += 2 * dy
            D2 += 2 * dz
            points.append((x, y, z))

    elif dy == max(dx, dy, dz):
        D1 = (2 * dx) - dy
        D2 = (2 * dz) - dy
        while y != y2:
            y += iy
            if D1 >= 0:
                x += ix
                D1 -= 2 * dy
            if D2 >= 0:
                z += iz
                D2 -= 2 * dy
            D1 += 2 * dx
            D2 += 2 * dz
            points.append((x, y, z))

    else:
        D1 = (2 * dy) - dz
        D2 = (2 * dx) - dz
        while z != z2:
            z += iz
            if D1 >= 0:
                y += iy
                D1 -= 2 * dz
            if D2 >= 0:
                x += ix
                D2 -= 2 * dz
            D1 += 2 * dy
            D2 += 2 * dx
            points.append((x, y, z))

    return points
