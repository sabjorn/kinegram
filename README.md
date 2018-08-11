# Kinegram

## Purpose
The purpose of this library and utility is to easily and procedurally generate [kinegrams](https://en.wikipedia.org/wiki/Barrier_grid_animation_and_stereography) ( barrier grid animations) from input images with parametric control of the grid spacing and width.

Furthermore, grid spacing and width will be controllable with respect to the properties of parallax. This is to allow the creation of animations which are driven by the movement of individuals through space through leveraging the difference in movement between sufficiently space foreground and background elements.

## Basics
Based on info found at this [making kinegrams](http://thinkzone.wlonk.com/Kinegram/MakingKinegrams.htm) site.

* from the top of one solid stripe to the top of the next solid stripe must be the same as the animation cycle length

* The clear stripes should be thinner than the solid stripes.
    * Thinner clear stripes will make the kinegram appear sharper but dimmer; whereas thicker clear stripes will make the kinegram appear brighter but blurrier.


## Observations
The above information should work well for situations where the stripes are overlayed directly onto the animation image. However, if there is some distance between the stripes and image, the apparent size between the stripes and image will change.

See: https://en.wikipedia.org/wiki/Visual_angle

Likely what is most important is to maintain the equality of the total stripe (black and clear) being the same as the total animation length.

## Calculations
```
V = 2arctan(S/2D)
```
where V is the visual angle
S is the height of the object
D is the distance of the object

to compensate for a change in D (for the stripes), the `visual angle` will be kept constant, while `D` changes and so `S` must be adjusted to compensate.

since the `visual angle` is a constant for both objects:

```
S1/D1 = S2/D2
```