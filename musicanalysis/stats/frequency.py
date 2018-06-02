from collections import defaultdict


class FrequencyDict(object):
    def __init__(self):
        self.freq_dict = defaultdict(int)

    def add(self, song, num=1):
        self.freq_dict[song] += num

    def sorted_list(self, descending):
        return [(key, self.freq_dict[key]) for key in sorted(self.freq_dict, key=self.freq_dict.get, reverse=descending)]

    def sorted_top_keys(self, num=None, descending=True):
        if num is None:
            num = len(self.freq_dict)
        return [key[0] for key in self.sorted_list(descending)][:num]

    def sorted_top_tuples(self, num=None, descending=True):
        if num is None:
            num = len(self.freq_dict)
        return [(key[0], key[1]) for key in self.sorted_list(descending)][:num]

    def keys_set(self):
        return set(self.freq_dict.keys())

    def __iter__(self):
        return ((key, value) for key, value in self.freq_dict.items())

    def __delitem__(self, key):
        del self.freq_dict[key]

    def __getitem__(self, key):
        return self.freq_dict[key]

    def __setitem__(self, key, value):
        self.freq_dict[key] = value

    def __str__(self):
        return str(self.freq_dict)

    def __len__(self):
        return len(self.freq_dict)

    def __repr__(self):
        return str(self.freq_dict)
