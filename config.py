from fyg import Config

config = Config({
	"defaults": {
		"port": 7777,
		"name": "anonymous",
		"server": "mariobalibrera.com"
	},
	"opponent": {
		"depth": 2,
		"tiny": True,
		"ai": "simple",
		"book": "random"
	},
	"rects": {},
	"sizes": {
		"width": 10,
		"height": 10
	},
	"colors": {
		"pitch": [0, 0, 0],
		"bright": [255, 255, 255],
		"black": [116, 69, 40],
		"white": [204, 166, 85],
		"green": [0, 255, 0],
		"red": [255, 0, 0],
		"moves": [200, 200, 200],
		"text": [92, 255, 42],
		"banner": [225, 225, 150]
	}
})

def setScale(doubled):
	MULT = doubled and 2 or 1
	UNIT = MULT * 32
	HALF = UNIT / 2
	sizes = config.sizes
	rects = config.rects
	sizes.update("mult", MULT)
	sizes.update("unit", UNIT)
	sizes.update("half", HALF)
	sizes.update("third", UNIT/3)
	sizes.update("chat", 5 * UNIT)
	rects.update("text", [0, UNIT * 8, UNIT * 3, HALF])
	rects.update("input", [0, HALF * 17, UNIT * 3, HALF])
	rects.update("banner", [UNIT, UNIT * 3, UNIT * 6, UNIT])
	rects.update("move", [UNIT * 8, UNIT, UNIT * 2, UNIT * 6])
	rects.update("chat", [3 * UNIT, 8 * UNIT, sizes.chat, UNIT])