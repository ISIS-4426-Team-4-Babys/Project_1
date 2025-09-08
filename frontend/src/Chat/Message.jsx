import { Card } from 'react-bootstrap';
import './Message.css';
import MarkdownRenderer from "./MarkdownRenderer";


export default function Message({ from, text }) {
  const isBot = from === 'bot';
  return (
    <div className={`messageRow ${isBot ? 'messageBot' : 'messageUser'}`}>
      <Card className={`${isBot ? 'text-dark' : 'bg-dark text-white'} ${isBot ? 'messageBotCard' : 'messageUserCard'}`}>
        {isBot
          ? <MarkdownRenderer markdownText={text} />
          : <Card.Text style={{ color: 'white', margin: '0 4px' }}>{text}</Card.Text>}
      </Card>
    </div>
  );
}