import numpy as np
from itertools import product
from pymclevel import alphaMaterials

try:
    import br
except ImportError:
    raise ImportError("Couldn't find 'br.py', have you downloaded it and put it "
            "in the same filter folder?")


displayName = "Block Coat"

inputs = (
    ("NOTE: Uses a selector string for 'find' and 'replace'.\n"
            "See `br.py` for the selector string syntax specifics. For simple "
            "use, just type a block id/name with optional data (i.e. \"stone\" "
            "for any stone or \"stone:3\" for diorite).", "label"),
    ("Find:", "string"),
    ("Replace:", "string"),
    ("Block:", alphaMaterials.Stone),
    ("Depth:", (1, 1, 256)),
    ("Expand to:", ("faces", "edges", "corners")),
    ("For every 'find' block in the selection, \"expands into\" the surrounding "
            "blocks up-to 'depth' blocks. If these blocks are the 'replace' "
            "blocks, replaces them with 'block'. 'expand into' dictates which "
            "directions it may expand, and each option includes the ones above.",
            "label"),
)


def perform(level, box, options):
    depth = options["Depth:"]
    expand_to = options["Expand to:"]

    find = br.selector("find", options["Find:"])
    replace = br.selector("replace", options["Replace:"])
    bid, bdata = options["Block:"].ID, options["Block:"].blockData

    # Get every matched block.
    mask = matches(level, box, find, replace, depth, expand_to)

    # Place the blocks.
    for ids, datas, slices in br.iterate(level, box, br.BLOCKS):
        cur_mask = mask[slices]

        # Set the blocks.
        ids[cur_mask] = bid
        datas[cur_mask] = bdata

    print "Finished coating."
    return


def matches(level, box, find, replace, depth, expand_to):
    # Create the mask arrays.
    find_mask = np.empty(br.shape(box), dtype=bool)
    replace_mask = np.empty_like(find_mask)

    # Find the masks for the whole selection.
    for ids, datas, slices in br.iterate(level, box, br.BLOCKS):
        find_mask[slices] = find.matches(ids, datas)
        replace_mask[slices] = replace.matches(ids, datas)


    # Preallocate the memory.
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



def expand(mask, replace_mask, shifted, unshifted, expand_to):
    # `shifted` and `unshifted` are just pre-allocated arrays.

    # Map of which adjacents are faces/edges/corners:
    #   Front:  Middle:   Back:
    #   C e C    e F e    C e C
    #   e F e    F - F    e F e
    #   C e C    e F e    C e C
    # Note that if each point is assigned a relative coordinate:
    # F = sum(abs(coords)) is 1
    # e = sum(abs(coords)) is 2
    # C = sum(abs(coords)) is 3

    # Note that the `adj` option is a hierachy, i.e. "corners" includes all 3
    # options, not just corners.
    max_sum_coords = 1 + ("faces", "edges", "corners").index(expand_to)
    assert max_sum_coords == 1 or max_sum_coords == 2 or max_sum_coords == 3


    # Store the array before added the points so that we don't accidentally add
    # unintended points by modifying `mask` within the loop.
    unshifted[:] = mask

    # Loop through all adjacent points.
    for adj in product((-1, 0, 1), repeat=3):
        sum_coords = sum(map(abs, adj))

        # Ignore if it's shifting by nothing.
        if sum_coords == 0:
            continue

        # Add this direction if it's within the permitted directions.
        if sum_coords <= max_sum_coords:
            br.shift_xzy(unshifted, *adj, out=shifted)
            mask |= (shifted & replace_mask)
