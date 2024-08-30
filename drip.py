import numpy as np
from collections import OrderedDict
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
    ("For every 'find' block in the selection, replace a random number of "
            "blocks in the given 'direction'; provided they are the 'replace' "
            "block. The number of blocks is a random number between the given "
            "'min depth' and 'max depth', inclusive of each. Each of these "
            "\"drips\" only have a 'chance' to be placed.", "label"),
    ("Find:", "string"),
    ("Replace:", "string"),
    ("Block:", alphaMaterials.Stone),
    ("Direction:", tuple(DIRECTIONS.keys())),
    ("Min depth:", (1, 0, 256)),
    ("Max depth:", (1, 0, 256)),
    ("Chance%:", (100.0, 0.0, 100.0)),
    br.selector_explain("find", "replace"),
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


    find = br.selector("find", options["Find:"])
    replace = br.selector("replace", options["Replace:"])
    bid, bdata = options["Block:"].ID, options["Block:"].blockData


    # Get the find and replace masks for the selection.
    find_mask = find.mask(level, box)
    replace_mask = replace.mask(level, box)

    # Get the block mask. This is where the real work is.
    mask = drip(find_mask, replace_mask, axis, sign, depth_min, depth_max,
            chance)

    # Place the blocks.
    for ids, datas, slices in br.iterate(level, box, br.BLOCKS):
        cur_mask = mask[slices]

        # Set the blocks.
        ids[cur_mask] = bid
        datas[cur_mask] = bdata


    print "Finished dripping."
    print "- find: {}".format(find)
    print "- replace: {}".format(replace)
    print "- block: ({}:{})".format(bid, bdata)
    print "- direction: {}".format(options["Direction:"].strip())
    print "- depth min: {}".format(depth_min)
    print "- depth max: {}".format(depth_max)
    print "- chance: {}%".format(options["Chance%:"])
    return



def drip(find_mask, replace_mask, axis, sign, depth_min, depth_max, chance):
    # Algorithm:
    # Mask the find and replace blocks in the whole selection. Shift the find
    # mask block by block, using logical & with the replace mask to select the
    # positions to place blocks. Do this min depth times, then we need to add the
    # random factor. To do this, cull a specific amount of the remaining matches
    # and pretend they don't match. The exact amount is dependant on the
    # difference between min and max depth. Then do the remaining shifts and &s,
    # until the max depth is reached.


    # Allocate some memory for shifting.
    shifted = np.empty_like(find_mask)

    # Use the original find matches as a seed, make sure to removed them after
    # the shifting.
    mask = np.copy(find_mask)

    # Randomly cull now.
    rand = np.random.random(find_mask.shape)
    mask &= (rand < chance)


    # Now do the initial shifting of the array, up to min depth.
    for _ in range(depth_min):
        br.shift(mask, sign, axis, out=shifted)

        # Add intersection to matches.
        mask |= (shifted & replace_mask)


    # Now simulate the random depth, if necessary.
    if depth_max > depth_min:
        # Cull a random amount of replace matches to simulate random depth.
        cull_prop = 1.0 / (depth_max - depth_min + 1)
        rand = np.random.random(replace_mask.shape)
        cull = (cull_prop > rand)
        replace_mask[cull] = False # pretend they didn't match.


        # Now do the final shifting and &ing.
        for _ in range(depth_max - depth_min):
            br.shift(mask, sign, axis, out=shifted)
            mask |= (shifted & replace_mask)


    # Remove the find matches which were added only to seed.
    mask[find_mask] = False
    return mask
