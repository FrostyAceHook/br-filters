import numpy as np
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


displayName = "Noise"


inputs = (
    ("If seed is non-zero, it can be used to reproduce this noise. Scale "
            "controls the general size of the fluctations. Octaves increase the "
            "chaos of the noise.", "label"),
    ("Essentially, the noise assigns all blocks a random value between 0 and 1, "
            "and then any 'replace' blocks which have a value between 'value "
            "min' and 'value max' get replaced. So:"
            "\n- ('value max' - 'value min') is roughly the proportion of "
                "blocks that will be replaced."
            "\n- for swirly noise, centre min and max around 0.5."
            "\n- for clumpy noise, keep min close to 0 (or max close to 1).",
            "label"),
    ("Replace:", "string"),
    ("Block:", alphaMaterials.Stone),
    ("Seed:", (0, 0, 10**9 - 1)),
    ("Scale:", (12, 1, 256)),
    ("Octaves:", (2, 1, 20)),
    ("Value min:", (0.0, 0.0, 1.0)),
    ("Value max:", (0.4, 0.0, 1.0)),
    br.selector_explain("replace"),
)


# Stuartian noise algorithm:
# Generate uniform random "nodes" spaced `scale` apart and then just linearly
# interpolate between them. Some distribution tweaking is performed at the end to
# make the distrubiton less centre-focussed. This may not be the most advanced
# noise algorithm, but it works just fine for these purposes and it is easy to
# implement in numpy, which is pretty much necessary to make it execute in <0.1s.
# Oh but uh, why not just use perlin?
# i din wanna


def perform(level, box, options):
    visualise = False # turn on for cool noise visualisation.

    # Get my seed.
    seed = options["Seed:"]
    if seed == 0:
        np.random.seed() # need a random seed to generate a random seed.
        seed = np.random.randint(1, 10**9)

    # Get those options.
    scale = options["Scale:"]
    octaves = options["Octaves:"]
    value_min = options["Value min:"]
    value_max = options["Value max:"]

    replace = br.selector("replace", options["Replace:"])
    bid, bdata = options["Block:"].ID, options["Block:"].blockData

    if value_max < value_min:
        raise Exception("'value max' cannot be smaller than 'value min'")


    # Seed this thing.
    np.random.seed(seed)


    # LETS MAAAAAKE SOOOME NOOOOOOOOOISE
    noise = stuartian_noise(br.shape(box), scale, octaves)


    if not visualise:
        # Place on the blocks where the noise values are within the specified
        # range.
        mask = ((value_min <= noise) & (noise <= value_max))

        # Iterate the blocks, in a holey manner because it's ok to just skip
        # missing chunks.
        for ids, datas, slices in br.iterate(level, box, br.BLOCKS, holey=True):
            # Line up the matches and the mask.
            cur_mask = (replace.matches(ids, datas) & mask[slices])

            # Knock em down.
            ids[cur_mask] = bid
            datas[cur_mask] = bdata

    else:
        # Time to acsend.
        # red - purple
        rainbow = np.array([14, 1, 4, 5, 3, 9, 11, 10])

        # Convert from the floating value to a value from 0 to len-1.
        noise *= len(rainbow) - 1

        wools = noise.astype(np.uint8)

        # Convert from the indices to the wool data values.
        for i in range(len(rainbow)):
            wools[wools == i] = rainbow[i] + 16
        wools -= 16

        # Taste the rainbow bitch.
        for ids, datas, slices in br.iterate(level, box, br.BLOCKS, holey=True):
            ids[:] = 35 # wool id.
            datas[:] = wools[slices]


    print "Finished making some noise."
    print "- seed: {}".format(seed)
    print "- scale: {}".format(scale)
    print "- octaves: {}".format(octaves)
    print "- value min: {}".format(value_min)
    print "- value max: {}".format(value_max)
    return



def stuartian_noise(shape, scale, octaves):
    # Create the noise in a slightly larger region than the selection to avoid
    # annoying issues with nodes being outside the region but obv still need to
    # access them. It will be cut down before returning. Note that the nodes
    # occur every `scale` blocks, that is there are `scale-1` blocks between
    # them.
    noise = np.random.random(map(lambda x: (x-2)/scale + 2, shape))
    # this numpy verion dunt got the new random generator.


    # If every block is a node, there is no need to do anything. The `correct`
    # function would leave data with scale=1 unchanged anyway so nothing is lost
    # by doing this. Also when scale=1 there is no excess space.
    if scale == 1:
        return noise


    # Do the linear interpolation along each axis. This is where the meat of the
    # smooth is. The lerp automatically fills in `scale-1` blocks between each
    # successive element, so this pads the selection to roughly the size of the
    # box, just slightly extended to incude the next node along.
    for axis in br.AXES:
        noise = lerp(noise, axis, scale)


    # Trim the noise back to the shape of the box.
    noise = noise[map(slice, shape)]


    # Correct the values of the noise, which shifts the distribution such that
    # it's roughly a uniform distribution. Currently, it's very centre-focussed
    # so this just spreads it towards the edges of 0 and 1.
    noise = correct(noise, scale)


    # Add the octaves by recursing with a smaller scale.
    if octaves > 1:
        # Impact value is arbitrary. It roughly controls how impactful the next
        # octave is to the noise. 0.6 seems pretty good at causing some chaos
        # without being all-consuming.
        impact = 0.6
        octave_scale = int((1.0 - impact) * scale)

        # Only keep going if the scale is at least 1.
        if octave_scale > 0:
            noise += impact * stuartian_noise(shape, octave_scale, octaves - 1)
            # Scale back to [0,1].
            noise /= (1 + impact)

    # Clip justin caseme.
    noise.clip(0.0, 1.0, out=noise)

    # Too easy.
    return noise



def lerp(data, axis, scale):
    # Note: don't go here w scale=1.
    assert scale > 1

    # Algorithm: repeat the data along the array in the positive direction until
    # the node, multiply that all by some weight array which scales it correctly.
    # Repeat for the negative direction and sum.

    # Simple count down from [1, 0) in `scale` number of steps.
    weights = np.arange(scale, 0, -1, dtype=float)
    weights /= scale

    # Pad the dimensions of weights and set it up along the correct axis.
    pad_dims = (None,)*axis + (slice(None),) + (None,)*(data.ndim - axis - 1)
    weights = weights[pad_dims]


    # Get the repeated data and weights for the positive "iteration".
    repeated_pos = np.repeat(data, scale, axis=axis)
    weighted_pos = np.tile(weights, data.shape)

    # Now for the negative, take selective slices as if we'd repeated the data
    # and weights in the negative direction. This is possible because `repeated`
    # and `weighted` are too long by `scale-1` along the axis since they repeat
    # the last element when it's in fact the end.
    slice_from = br.slice_along(axis, scale - 1, None)
    slice_until = br.slice_along(axis, None, 1 - scale)

    repeated_neg = repeated_pos[slice_from]
    weighted_neg = 1 - weighted_pos[slice_until]
    # To avoid double-counting at nodes, just set each node weight to 0.
    weighted_neg[br.slice_along(axis, None, None, scale)] = 0.0


    # Do positive direction, cutting down to the correct size.
    lerped = weighted_pos[slice_until] * repeated_pos[slice_until]

    # Do negative direction. This doesn't need any cutting just because of how
    # it's setup.
    lerped += weighted_neg * repeated_neg

    return lerped



def correct(noise, scale):
    # Visualisation of the distribution inversion:
    # https://www.desmos.com/calculator/z5oj1dha65

    spread = lambda x: x*x*(3 - 2*x)
    s = spread(spread(noise))


    # The correction needed actually depends on the scale, smaller scales just
    # naturally have a more uniform distribution since a greater proportion of
    # the noise is literally a uniform distribution (the nodes). So, mix in a bit
    # of the uncorrected noise to essentially reduce the smoothness of the smooth
    # function.
    scale_2_2 = scale ** 2.2
    return (noise + (scale_2_2 - 1) * s) / scale_2_2

    # bunch of really rough scribbling/working if u wanna cop a geez.
    # https://www.desmos.com/calculator/yk9j6orqpg
