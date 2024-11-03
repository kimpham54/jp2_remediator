from jp2_remediator.box_reader import BoxReader


class BoxReaderFactory:

    def get_reader(self, file_path):
        """
        Create a BoxReader instance for a given file path.
        :param file_path: The path to the file to be read.
        :return: A BoxReader instance.
        """
        return BoxReader(file_path)
