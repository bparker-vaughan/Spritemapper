import logging
from os import path
from spritecss import SpriteMap
from spritecss.config import CSSConfig

logger = logging.getLogger(__name__)

class SpriteDirsMapper(object):
    """Maps sprites to spritemaps by using the sprite directory."""

    def __init__(self, sprite_dirs=None, recursive=True):
        self.sprite_dirs = sprite_dirs
        self.recursive = recursive

    @classmethod
    def from_conf(cls, conf):
        # TODO Make recursion a configurable option.
        return cls(conf.sprite_dirs)

    def _map_sprite_ref(self, sref):
        if self.sprite_dirs is None:
            return path.dirname(sref.fname)

        for sdir in self.sprite_dirs:
            prefix = path.commonprefix((sdir, sref.fname))
            if prefix == sdir:
                if self.recursive:
                    submap = path.dirname(path.relpath(sref.fname, sdir))
                    return path.join(sdir, submap)
                else:
                    return sdir

        raise ReferenceError

    def __call__(self, sprite):
        try:
            return self._map_sprite_ref(sprite)
        except ReferenceError:
            logger.info("not mapping %r", sprite)

class SpriteMapCollector(object):
    """Collect spritemap listings from sprite references."""

    def __init__(self, conf=None):
        if conf is None:
            conf = CSSConfig()
        self.conf = conf
        self._maps = {}

    def __iter__(self):
        return self._maps.itervalues()

    def map_sprite_refs(self, srefs, mapper=None):
        if mapper is None:
            mapper = SpriteDirsMapper()

        for sref in srefs:
            smap_fname = mapper(sref)
            smap = self._maps.get(smap_fname)
            if smap is None:
                smap = self._maps[smap_fname] = SpriteMap(smap_fname)
            if sref not in smap:
                smap.append(sref)

    def map_file(self, fname, mapper=None):
        """Convenience function to map the sprites of a given CSS file."""
        from spritecss.css import CSSParser
        from spritecss.finder import find_sprite_refs

        with open(fname, "rb") as fp:
            parser = CSSParser.read_file(fp)
            evs = list(parser.iter_events())

        conf = CSSConfig(evs, base=self.conf, root=path.dirname(fname))
        srefs = find_sprite_refs(evs, source=fname, conf=conf)

        if mapper is None:
            mapper = SpriteDirsMapper.from_conf(conf)

        self.map_sprite_refs(srefs, mapper=mapper)

def print_spritemaps(smaps):
    for smap in sorted(smaps, key=lambda sm: sm.fname):
        print smap.fname
        for sref in smap:
            print "-", sref
        print

def _map_and_print(fnames):
    smaps = SpriteMapCollector()
    for fname in fnames:
        smaps.map_file(fname)
    print_spritemaps(smaps)

def _map_fnames(fnames):
    import sys
    import json
    from . import SpriteRef

    smaps = SpriteMapCollector()

    for fname in fnames:
        with sys.stdin if (fname == "-") else open(fname, "rb") as fp:
            (src_fname, srefs) = json.load(fp)

        srefs = [SpriteRef(sref, source=src_fname) for sref in srefs]
        smaps.map_sprite_refs(srefs)
        print >>sys.stderr, "mapped", len(srefs), "sprites in", src_fname

    json.dump([(smap.fname, map(str, smap)) for smap in smaps], sys.stdout, indent=2)

def main():
    import sys
    import logging

    logging.basicConfig(level=logging.DEBUG)
    fnames = sys.argv[1:]

    if all(fname.endswith(".css") for fname in fnames):
        _map_and_print(fnames)
    elif fnames:
        _map_fnames(fnames)
    else:
        src_dir = path.join(path.dirname(__file__), "..")
        example_fn = "ext/Spritemapper/css/example_source.css"
        _map_and_print([path.normpath(path.join(src_dir, example_fn))])

if __name__ == "__main__":
    main()