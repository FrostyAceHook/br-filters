import numpy as np
from collections import OrderedDict
from pymclevel import alphaMaterials

try:
    import br
except ImportError:
    raise ImportError("Couldn't find 'br.py', have you downloaded it and put it "
            "in the same filter folder?")


displayName = "Drip-ip"

DIRECTIONS = OrderedDict([
    # bruh why cant u start an option w a '-'??
    (" -y", (-1, br.AXIS_Y)),
    (" -x", (-1, br.AXIS_X)),
    (" -z", (-1, br.AXIS_Z)),
    ("+y", (1, br.AXIS_Y)),
    ("+x", (1, br.AXIS_X)),
    ("+z", (1, br.AXIS_Z)),
])

inputs = (
    ("NOTE: Uses a selector string for 'find' and 'replace'.\n"
            "See `br.py` for the selector string syntax specifics. For simple "
            "use, just type a block id/name with optional data (i.e. \"stone\" "
            "for any stone or \"stone:3\" for diorite).", "label"),
    ("Find:", "string"),
    ("Replace:", "string"),
    ("Block:", alphaMaterials.Stone),
    ("Direction:", tuple(DIRECTIONS.keys())),
    ("Min depth:", (1, 0, 256)),
    ("Max depth:", (1, 0, 256)),
    ("Chance%:", (100.0, 0.0, 100.0)),
    ("For every 'find' block in the selection, replace a random number of "
            "blocks in the given 'direction'; provided they are the 'replace' "
            "block. The number of blocks is a random number between the given "
            "'min depth' and 'max depth', inclusive of each. Each of these "
            "\"drips\" only have a 'chance' to be placed.", "label"),
)


def perform(level, box, options):
    # Get the options.
    sign, axis = DIRECTIONS[options["Direction:"]]
    depth_min = options["Min depth:"]
    depth_max = options["Max depth:"]
    chance = options["Chance%:"] / 100.0

    # dumas check.
    if depth_max < depth_min:
        raise Exception("'max depth' cannot be smaller than 'min depth'")

    print "Direction: {}".format(options["Direction:"].strip())
    print "Min depth: {}".format(depth_min)
    print "Max depth: {}".format(depth_max)
    print "Chance: {}%".format(options["Chance%:"])


    find = br.selector("find", options["Find:"])
    replace = br.selector("replace", options["Replace:"])
    bid, bdata = options["Block:"].ID, options["Block:"].blockData

    # Get the block mask. This is where the real work is.
    mask = matches(level, box, find, replace, axis, sign, depth_min, depth_max,
            chance)

    # Place the blocks.
    for ids, datas, slices in br.iterate(level, box, br.BLOCKS):
        cur_mask = mask[slices]

        # Set the blocks.
        ids[cur_mask] = bid
        datas[cur_mask] = bdata

    print "Finished dripping."
    return


def matches(level, box, find, replace, axis, sign, depth_min, depth_max, chance):
    # Algorithm:
    # Mask the find and replace blocks in the whole selection. Shift the find
    # mask block by block, using logical & with the replace mask to select the
    # positions to place blocks. Do this min depth times, then we need to add the
    # random factor. To do this, cull a specific amount of the remaining matches
    # and pretend they don't match. The exact amount is dependant on the
    # difference between min and max depth. Then do the remaining shifts and &s,
    # until the max depth is reached.


    # Create the mask arrays.
    find_mask = np.empty(br.shape(box), dtype=bool)
    replace_mask = np.empty_like(find_mask)
    shifted = np.empty_like(find_mask) # used as memory when shifting.


    # Find the masks for the whole selection.
    for ids, datas, slices in br.iterate(level, box, br.BLOCKS):
        find_mask[slices] = find.matches(ids, datas)
        replace_mask[slices] = replace.matches(ids, datas)


    # Use the original find matches as a seed, make sure to removed them after
    # the shifting.
    mask = np.copy(find_mask)

    # Randomly cull now.
    rand = np.random.random_sample(br.shape(box))
    mask &= (rand < chance)


    # Now do the initial shifting of the array, up to min depth.
    for _ in range(depth_min):
        br.shift(mask, sign, axis, out=shifted)

        # Add intersection to matches.
        mask |= (shifted & replace_mask)


    # Now simulate the randomness, if necessary.
    if depth_max > depth_min:
        # Cull a random amount of replace matches to simulate random depth.
        cull_prop = 1.0 / (depth_max - depth_min + 1)
        cull = (cull_prop > np.random.random(replace_mask.shape))
        replace_mask[cull] = 0


        # Now do the final shifting and &ing.
        for _ in range(depth_max - depth_min):
            br.shift(mask, sign, axis, out=shifted)
            mask |= (shifted & replace_mask)


    # Remove the find matches which were added only to seed.
    mask[find_mask] = False
    return mask
