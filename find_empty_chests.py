import time
from pymclevel import TileEntity

displayName = "Find empty chests"

inputs = (
    ("Gaming?", True), # does ntohing.
    ("Check console for result.", "label"),
)

def perform(level, box, options):
    start = time.time()

    # Store all coordinates of empty chests.
    all_coords = []

    print("Total chunks: {}".format(sum(1 for _ in level.getChunkSlices(box))))

    count = 0
    for chunk, slices, point in level.getChunkSlices(box):
        count += 1
        if count%5==0:
            print("Chunk: {}".format(count))

        for te in chunk.TileEntities:
            if TileEntity.pos(te) not in box:
                continue

            if te["id"].value not in {"Chest", "minecraft:chest"}:
                continue

            if len(te["Items"]) == 0:
                all_coords.append(TileEntity.pos(te))

    print("Found {} empty chest{}.".format(len(all_coords), "s" if len(all_coords)!=1 else ""))
    for coord in all_coords:
        print("({}, {}, {})".format(*coord))

    end = time.time()
    print("Finished in {} seconds.".format(round(end-start, 2)))
    return