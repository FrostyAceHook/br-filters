import br
import numpy as np
from pymclevel import alphaMaterials

displayName = "Gridify 3"
# i have no idea what gridify 1 was. but ig i better make this gridify 3...
#  - me, moments before the creation of gridify 3


inputs = (
    ("Replace except?", True),
    ("Replace:", alphaMaterials.Air),
    ("Block 1:", alphaMaterials.Stone),
    ("Block 2:", alphaMaterials.Cobblestone),
    ("Swap blocks?", False),
    ("issa grid innit. Swap blocks is a purely convenience option.", "label"),
)


def perform(level, box, options):
    # Get some options.
    replace = br.from_options(options, "Replace")
    place = br.from_options(options, "Block", count=2)
    swap = int(options["Swap blocks?"])

    # Make true/false alternating in a grid the size of the selection.
    w, l, h = br.shape(box)
    odd = (np.arange(w)[:, None, None] + np.arange(l)[:, None] + np.arange(h) +
            swap) % 2 # cheekily incorperate the swap option.

    # Do the thang.
    for ids, datas, slices in br.iterate(level, box, method=br.SLICES):
        # Get the block matches (she was a moth to the flame type shit).
        mask = replace.matches(ids, datas)

        # Get the current slice of the odd array.
        cur_odd = odd[slices]

        # Set ecah block type.
        for i, (bid, bdata) in enumerate(place):
            # Only place on "replace" block and at either odd or even positions.
            cur_mask = (mask & (cur_odd == i))
            ids[cur_mask] = bid
            datas[cur_mask] = bdata


    level.markDirtyBox(box)
    print "Finished gridifying."
    # you ever just wanna eat a shoe.
    # i eat sneakers.
    return
