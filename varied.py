import time
from pymclevel import alphaMaterials
import random as rdm
import numpy as np

displayName = "Varied Replace"

inputs = (
    ("\n\n\n\n", "label"),
    ("Find except?", True),
    ("Find:", alphaMaterials.Air),
    ("IMPORTANT: Must run this filter twice without changing the selection (literally just run and then run again) to handle a very strange mcedit bug where it skips chunks when using certain backend methods (which this uses). The bug doesn't happen everytime but seems to be much more likely with larger selections.", "label"),
    ("\n\n\n\n", "label"),
    ("Block 1:", alphaMaterials.Stone),
    ("Block 1 weight:", (1, 0, 32767)),
    ("Block 2:", "blocktype"),
    ("Block 2 weight:", (0, 0, 32767)),
    ("Block 3:", "blocktype"),
    ("Block 3 weight:", (0, 0, 32767)),
    ("Block 4:", "blocktype"),
    ("Block 4 weight:", (0, 0, 32767)),
)



def perform(level, box, options):
    start = time.time()

    # Check weight is non-zero.
    if sum((options["Block "+str(x)+" weight:"] for x in (1,2,3,4))) == 0:
        raise Exception("Must set the weight of at least one block to non-zero, champ.")


    # Get a bunch of options.

    find_except = options["Find except?"]
    find_block_id = options["Find:"].ID
    find_block_data = options["Find:"].blockData

    block1_id = options["Block 1:"].ID
    block2_id = options["Block 2:"].ID
    block3_id = options["Block 3:"].ID
    block4_id = options["Block 4:"].ID
    block_ids = (block1_id, block2_id, block3_id, block4_id)

    block1_data = options["Block 1:"].blockData
    block2_data = options["Block 2:"].blockData
    block3_data = options["Block 3:"].blockData
    block4_data = options["Block 4:"].blockData
    block_datas = (block1_data, block2_data, block3_data, block4_data)

    block1_cutoff = options["Block 1 weight:"]
    block2_cutoff = options["Block 2 weight:"] + block1_cutoff
    block3_cutoff = options["Block 3 weight:"] + block2_cutoff
    block4_cutoff = options["Block 4 weight:"] + block3_cutoff


    # Print the total chunk count.
    print("Total chunks: {}".format(sum(1 for _ in level.getChunkSlices(box))))


    # Iterate through the chunks, find the blocks to replace, get the proportions
    # and set them blocks.
    count = 0
    for chunk, slices, point in level.getChunkSlices(box):
        # Note that the format of each coord in this function is [x,z,y].

        count += 1
        if count%5 == 0:
            print("Chunk: {}".format(count))

        ids = chunk.Blocks[slices]
        data = chunk.Data[slices]
        ord_dt = "int32"
        coords_dt = "int32,int32,int32"

        # Find the coords where id or data matches.
        id_coords = np.array(np.where(ids == find_block_id)).astype(ord_dt)
        data_coords = np.array(np.where(data == find_block_data)).astype(ord_dt)

        # View each coord as a single data point. Surely theres a way to do this
        # without two transposes :skull:
        id_coords = id_coords.T.reshape(-1).view(coords_dt).T
        data_coords = data_coords.T.reshape(-1).view(coords_dt).T


        # Find the coords where both id and data matches and reset view to the
        # full x,z,y coord.
        coords = np.intersect1d(id_coords, data_coords)


        # Do selection inversion if needed.
        if find_except:
            # Get dimensions of the slice in this chunk.
            slice_sizes = [slices[i].stop - slices[i].start for i in range(3)]

            # Get a list of all coordinates selected in this chunk.
            xx, yy, zz = np.meshgrid(*[np.arange(slice_sizes[i]) for i in range(3)])
            all_coords = np.vstack((xx.flatten(), yy.flatten(), zz.flatten()))
            all_coords = all_coords.T.reshape(-1).view(coords_dt).T

            # Now only use coords that don't match the find block.
            coords = np.setdiff1d(all_coords, coords)


        # Now we have a list of every coordinate to replace, as a vertical array
        # where each row is a coordinate in x,z,y order.
        coords = coords.view(ord_dt).reshape(-1, 3)
        num_coords = coords.shape[0]


        # Find the amounts of each block.
        block_counts = [0]*4
        for _ in range(num_coords):
            # Generate a random integer.
            rand = rdm.randint(0, block4_cutoff - 1)
            # Depending on which interval it lands in, add one block of that
            # type.
            if rand < block1_cutoff:
                block_counts[0] += 1
            elif rand < block2_cutoff:
                block_counts[1] += 1
            elif rand < block3_cutoff:
                block_counts[2] += 1
            else:
                block_counts[3] += 1


        # Cheeky shuffle so that we can just take direct subsections of the
        # coords and set.
        np.random.shuffle(coords)

        # Now go through each subsection of the coords and set them to the
        # corresponding block.
        cur = 0
        for i in range(4):
            # Get the current subsection of coords.
            cur_coords = coords[cur:cur + block_counts[i], :]
            cur += block_counts[i]

            # Set the blocks.
            ids[cur_coords[:,0], cur_coords[:,1], cur_coords[:,2]] = block_ids[i]
            data[cur_coords[:,0], cur_coords[:,1], cur_coords[:,2]] = block_datas[i]



    level.markDirtyBox(box)
    end = time.time()
    print("Finished in {} seconds.".format(round(end-start, 2)))
    return
