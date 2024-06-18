import { Box } from '@mui/material';
import Markdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface IMarkdownPanel {
    content: string
}

const MarkdownPanel: React.FC<IMarkdownPanel> = ({ content }) => {
    return (
        <Box sx={{ p: 2  }} >
            <Markdown children={content} remarkPlugins={[remarkGfm]} />
        </Box>
    );
};

export default MarkdownPanel;