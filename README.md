# br-filters

some mcedit 1.0 filters to help build maps.

to install, download any filters you want, download [br.py](./br.py) and chuck
all that in the mcedit filter folder.

- particularly useful:
    - [smooth](./smooth.py)
    - [noise](./noise.py)
    - [varied](./varied.py)
- personal favourite: [block coat](./block_coat.py)
- ugly middle child: [find empty chests](./find_empty_chests.py)
- all these filters run pretty much instantly for any selection (turn off undo to
        see the true speed)
- or charle.

# some tips

Most of these filters are simply an iteration over all the blocks in the
selection, changing each block if it meets certain conditions.

A lot of filters use a "selector string", which is a way to evaluate whether this
block is included or not (note it's not just used for replacement, often it's
used for an auxiliary 'find' block or similar). Details for the selector string
can be found in [br.py](./br.py)

A simple example is the [grid](./grid.py) filter. This replaces all blocks that
are selected by the 'replace' selector with either "block 1" or "block 2",
depending on the coordinates of the block being placed. This creates the grid
fill, which may only replace some blocks in the selection.

Another filter is [block coat](./block_coat.py). This filter initially selects
using 'find' selector. From these blocks, it expands to adjacent blocks that are
selected by the 'replace' selector, and only in directions dictated by 'expand
to'. The blocks that were expanded-to are replaced by 'block'. This expansion and
replacement is then repeated another 'depth - 1' times.

### slightly more advanced usage

These filters can do a lot of general operations when used in combination with
one another. A common pattern is using filters to place temporary blocks,
refining the placement of those temporary blocks, then replacing them with the
desired blocks.

For example, to create some blended ore deposits you might want:

1. create deposits: [noise](./noise.py) with "block = iron ore"
2. select surroundings: [block coat](./block_coat.py) with "find = iron ore",
        "replace = except air", "block = sponge"
3. select only surface: [block coat](./block_coat.py) with "find = air", "replace
        = sponge", "block = wet sponge"
4. reset under surface: replace "sponge" with old blocks, depends on the previous
        blocks.
5. do the blending: [varied](./varied.py) with "replace = wet sponge", "block 1 =
        iron ore", "block 2 = granite", "block 3 = cobblestone"

This is just one example, but with enough temp block ids you can do pretty much
anything.
