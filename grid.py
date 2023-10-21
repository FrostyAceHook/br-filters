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

    # Make an array of the blocks the size of the selection, in the grid fill.
    # This is then selectively copied into the level to achive the grid.
    bids, bdatas = blocks(box, place, swap)

    # Do the thang.
    for ids, datas, slices in br.iterate(level, box, method=br.SLICES):
        # Get the block matches (she was a moth to the flame type shit).
        mask = replace.matches(ids, datas)

        # Get the current slice of the blocks.
        cur_bids = bids[slices]
        cur_bdatas = bdatas[slices]

        # Set the blocks.
        ids[mask] = cur_bids[mask]
        datas[mask] = cur_bdatas[mask]


    level.markDirtyBox(box)
    print "Finished gridifying."
    # you ever just wanna eat a shoe.
    # i eat sneakers.
    return


def blocks(box, place, swap):
    # Create the storage arrays to fill with the grid pattern.
    bids = np.empty(br.shape(box), dtype=np.uint16)
    bdatas = np.empty_like(bids)

    # Calculate the indices to every second block.
    w, l, h = br.shape(box)
    index = (np.arange(w)[:, None, None] + np.arange(l)[:, None] + np.arange(h) +
            swap) % 2 # cheekily incorperate the swap option.

    # Put the correct data in.
    bids[index == 0] = place.ids[0]
    bids[index == 1] = place.ids[1]
    bdatas[index == 0] = place.datas[0]
    bdatas[index == 1] = place.datas[1]

    return bids, bdatas
