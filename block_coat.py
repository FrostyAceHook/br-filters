import br
import numpy as np
from itertools import product
from pymclevel import alphaMaterials

displayName = "Block Coat"

inputs = (
    ("Find except?", False),
    ("Find:", alphaMaterials.Air),
    ("Replace except?", True),
    ("Replace:", alphaMaterials.Air),
    ("Block:", alphaMaterials.Stone),
    ("Depth:", (1, 1, 256)),
    ("For every \"find\" block in the selection, searches the blocks around it "
            "that are the \"replace\" block, to a maximum depth of \"depth\", "
            "and replaces them with \"block\".", "label"),
)


def perform(level, box, options):
    depth = options["Depth:"]

    replace = br.from_options(options, "Replace")
    find = br.from_options(options, "Find")

    bid, bdata = options["Block:"].ID, options["Block:"].blockData

    # Get every matched block.
    mask = matches(level, box, find, replace, depth)

    # Place the blocks.
    for ids, datas, slices in br.iterate(level, box, method=br.SLICES):
        cur_mask = mask[slices]

        # Set the blocks.
        ids[cur_mask] = bid
        datas[cur_mask] = bdata

    print "Finished coating."
    return


def matches(level, box, find, replace, depth):
    # Create the mask arrays.
    find_mask = np.empty(br.shape(box), dtype=bool)
    replace_mask = np.empty_like(find_mask)

    # Find the masks for the whole selection.
    for ids, datas, slices in br.iterate(level, box, method=br.SLICES):
        find_mask[slices] = find.matches(ids, datas)
        replace_mask[slices] = replace.matches(ids, datas)


    # Preallocate the memory.
    shifted = np.empty_like(find_mask)
    unshifted = np.empty_like(find_mask)

    # Copy the find array and shift it around while matching with replaceable
    # blocks. Note the original find matches are there only as a seed and will be
    # removed after the coating.
    mask = np.copy(find_mask)
    for _ in range(depth):
        # Need to store the array for each depth pass to only include adjacents
        # and not accidentally count some diagonals.
        unshifted[:] = mask
        for by, axis in product((-1, 1), br.AXES):
            # Shift the array into `shifted` to match neighbouring blocks.
            br.shift(unshifted, by, axis, out=shifted)

            # Add intersection to matches.
            mask |= (shifted & replace_mask)

    # Remove the find matches which were added only to seed.
    mask[find_mask] = False
    return mask
