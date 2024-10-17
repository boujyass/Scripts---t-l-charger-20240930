using System.Numerics;
using UnityEngine;
using Leap;
using Vector3 = UnityEngine.Vector3;


public class HandDirectionLogger : MonoBehaviour
{
    // Reference to the LeapServiceProvider to access tracking data
    private LeapServiceProvider leapProvider;
    public OSC osc; 
    void Start()
    {
        // Find the LeapServiceProvider in the scene
        leapProvider = FindObjectOfType<LeapServiceProvider>();
        if (leapProvider == null)
        {
            Debug.LogError("LeapServiceProvider not found in the scene. Please ensure it is added.");
        }
    }

    void Update()
    {
        // Get the current frame containing hand tracking data
        Frame frame = leapProvider.CurrentFrame;

        // Check if any hands are detected in the frame
        if (frame.Hands.Count > 0)
        {
            foreach (Hand hand in frame.Hands)
            {
                // Determine if the hand is left or right
                string handType = hand.IsLeft ? "Left Hand" : "Right Hand";

                // Get the hand's direction vector
                Vector3 handDirection = hand.Direction;
                
                
                // Get the index finger of the hand
                Finger indexFinger = hand.fingers[1];

                if (indexFinger != null)
                {
                    // Get the index finger's direction vector
                    Vector3 indexDirection = indexFinger.Direction;

                    // Log the hand and index finger directions to the console
                    Debug.Log($"{handType} Direction: {handDirection}");
                    Debug.Log($"{handType} Index Finger Direction: {indexDirection}");
                }
                else
                {
                    Debug.Log($"{handType} Index Finger not found.");
                }
                
                
                // Send OSC message
                OscMessage message = new OscMessage();
                string handIdentifier = hand.IsLeft ? "left" : "right";
                message.address = $"/hand/{handIdentifier}/direction";
                message.values.Add(handDirection.x);
                message.values.Add(handDirection.y);
                message.values.Add(handDirection.z);
                osc.Send(message);
            }
        }
    }
}