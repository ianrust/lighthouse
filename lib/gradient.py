from color import Color, interpolate_colors

from lib.utils import interpolate_value

class Gradient(object):
	def __init__(
		self,
		seconds: float,
        color_1: Color,
        color_2: Color,
        brightness: float,
        scroll_speed: float
    ):
    	self.seconds = seconds
    	self.color_1 = color_1
    	self.color_2 = color_2
    	self.brightness = brightness
    	self.scroll_speed = scroll_speed

    def __repr__(self):
        return '<Gradient seconds={seconds} color_1={color_1} color_2={color_2} brighness={brightness} scroll_speed={scroll_speed} />'.format(
            seconds=self.seconds,
            color_1=self.color_1,
            color_2=self.color_2,
            brightness=self.brightness,
            scroll_speed=self.scroll_speed
            )

def interpolate_gradients(gradient_1: Gradient, gradient_2: Gradient, ratio: float) -> Gradient:
	gradient = Gradient(
			interpolate_value(gradient_1.seconds, gradient_2.seconds, ratio),
			interpolate_colors(gradient_1.color_1, gradient_2.color_1, ratio),
			interpolate_colors(gradient_1.color_2, gradient_2.color_2, ratio),
			interpolate_value(gradient_1.brightness, gradient_2.brightness, ratio),
			interpolate_value(gradient_1.scroll_speed, gradient_2.scroll_speed, ratio),
		)
	return gradient
