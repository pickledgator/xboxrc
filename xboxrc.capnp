@0xea58bcac2fa96450;

using Cxx = import "/capnp/c++.capnp";
$Cxx.namespace("xboxrc");

struct Xbox @0x8000000000000050
{
	enum EventType {
		none @0;
		button @1;
		axis @2;
	}

	enum EventField {
		none @0;
		a @1;
		b @2;
		c @3;
		x @4;
		y @5;
		z @6;
		start @7;
		select @8;
		mode @9;
		thumbl @10;
		thumbr @11;
		dpadUp @12;
		dpadDown @13;
		dpadLeft @14;
		dpadRight @15;	
	}

  timestamp		@0 : UInt64;
  type			@1 : EventType;
  field 		@2 : EventField;
  value 		@3 : Int32;
}