import numpy as np
from itertools import product
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


displayName = "Coat"


inputs = (
    ("For every 'find' block in the selection, \"expands into\" the surrounding "
            "blocks up-to 'depth' blocks. If these blocks are the 'replace' "
            "blocks, replaces them with 'block'. 'expand into' dictates which "
            "directions it may expand, and each option includes the ones above.",
            "label"),
    ("Find:", "string"),
    ("Replace:", "string"),
    ("Block:", alphaMaterials.Stone),
    ("Depth:", (1, 1, 256)),
    ("Expand to:", ("faces", "edges", "corners")),
    br.selector_explain("find", "replace"),
)


def perform(level, box, options):
    depth = options["Depth:"]
    expand_to = options["Expand to:"]

    find = br.selector("find", options["Find:"])
    replace = br.selector("replace", options["Replace:"])
    bid, bdata = options["Block:"].ID, options["Block:"].blockData


    # Get the find and replace masks for the selection.
    find_mask = find.mask(level, box)
    replace_mask = replace.mask(level, box)

    # Get every matched block.
    mask = coat(find_mask, replace_mask, depth, expand_to)

    # Place the blocks.
    for ids, datas, slices in br.iterate(level, box, br.BLOCKS):
        cur_mask = mask[slices]

        # Set the blocks.
        ids[cur_mask] = bid
        datas[cur_mask] = bdata


    print "Finished coating."
    print "- find: {}".format(find)
    print "- replace: {}".format(replace)
    print "- block: ({}:{})".format(bid, bdata)
    print "- depth: {}".format(depth)
    print "- expand to: {}".format(expand_to)
    return



def coat(find_mask, replace_mask, depth, expand_to):
    # Preallocate some memory for shifting.
    shifted = np.empty_like(find_mask)
    unshifted = np.empty_like(find_mask)

    # Expand the mask `depth` times. Note the original find matches are there
    # only as a seed and will be removed after the coating.
    mask = np.copy(find_mask)
    for _ in range(depth):
        expand(mask, replace_mask, shifted, unshifted, expand_to)

    # Remove the find matches which were added only to seed.
    mask[find_mask] = False

    return mask



# Map of which adjacents are faces/edges/corners:
#   Front:  Middle:   Back:
#   C e C    e F e    C e C
#   e F e    F - F    e F e
#   C e C    e F e    C e C
# So, if each point is assigned a relative coordinate:
# F = sum(abs(coords)) is 1
# e = sum(abs(coords)) is 2
# C = sum(abs(coords)) is 3
# Therefore the expansion directions can be reframed in terms of max coord sums.
# Note that the `adj` option is a hierachy, i.e. "corners" includes all 3
# options, not just corners.
MAX_COORD_SUM = {
    "faces": 1,
    "edges": 2,
    "corners": 3,
}

# Precompute all the adjacent coord sums.
ADJACENTS = [(pos, sum(map(abs, pos))) for pos in br.ADJACENTS]

def expand(mask, replace_mask, shifted, unshifted, expand_to):
    # `shifted` and `unshifted` are just pre-allocated arrays.

    # Get a list of all the adjacent corners we will expand to.
    max_coord_sum = MAX_COORD_SUM[expand_to]
    adjacents = [pos for pos, sumc in ADJACENTS if sumc <= max_coord_sum]

    # Store the array before added the points so that we don't accidentally add
    # unintended points by modifying `mask` within the loop.
    unshifted[:] = mask

    # Loop through and add all adjacent points.
    for adj in adjacents:
        br.shift_xzy(unshifted, *adj, out=shifted)
        mask |= (shifted & replace_mask)
